import scrapy
import re
import json


class TunisietravailSpider(scrapy.Spider):
    """
    Spider pour tunisietravail.net - PredictIT project
    Scrape l'ensemble des offres des catégories IT sans restriction de limite.
    """

    name = "tunisietravail"
    allowed_domains = ["tunisietravail.net"]

    start_urls = [
        "https://www.tunisietravail.net/category/offres-d-emploi-et-recrutement/it/developpeur/",
        "https://www.tunisietravail.net/category/offres-d-emploi-et-recrutement/it/developpeur-web/",
        "https://www.tunisietravail.net/category/offres-d-emploi-et-recrutement/it/developpeur-net-c-vb-java-jee/",
        "https://www.tunisietravail.net/category/offres-d-emploi-et-recrutement/it/developpeur-ios-developpeur-android/",
        "https://www.tunisietravail.net/category/offres-d-emploi-et-recrutement/it/administrateur-base-de-donnee/",
        "https://www.tunisietravail.net/category/offres-d-emploi-et-recrutement/it/administrateur-reseaux/",
        "https://www.tunisietravail.net/category/offres-d-emploi-et-recrutement/it/administrateur-systeme/",
        "https://www.tunisietravail.net/category/offres-d-emploi-et-recrutement/it/webdesigner-webmaster/",
    ]

    NOISE_KEYWORDS = [
        "formateur", "formatrice",
        "marketing digital", "chargé marketing", "chargée marketing",
        "community manager", "social media",
        "commercial", "vente", "vendeur", "vendeuse",
        "ressources humaines", "assistant.e ressources humaines",
        "sourcing et recrutement",
    ]

    def parse(self, response):
        # 1. Extraction des liens vers les offres individuelles
        offer_links = response.css("h2 a::attr(href), article h2 a::attr(href), .post-title a::attr(href)").getall()

        for link in set(offer_links):
            if link and "/category/" not in link and "/tag/" not in link:
                yield response.follow(link, callback=self.parse_offer)

        # 2. Pagination : reconstruction de l'URL de page suivante à partir
        # de l'URL de catégorie ACTUELLE (bornée aux start_urls) plutôt que
        # de suivre un lien générique -- c'est ce garde-fou qui évite de
        # fuir vers les pages d'archive globale du site (bug déjà rencontré).
        if not any(response.url.startswith(su) for su in self.start_urls):
            return

        category_base = re.sub(r"page/\d+/$", "", response.url)
        current_page_match = re.search(r"/page/(\d+)/", response.url)
        current_page = int(current_page_match.group(1)) if current_page_match else 1
        next_page_url = f"{category_base}page/{current_page + 1}/"

        all_hrefs = response.css("a::attr(href)").getall()
        if next_page_url in all_hrefs:
            yield response.follow(next_page_url, callback=self.parse)

    def parse_offer(self, response):
        # Titre : ".PostHead h1" confirmé sur le vrai HTML, gardé en 1er
        title = response.css(".PostHead h1::text, h1::text, .entry-title::text").get()
        if title:
            title = title.strip()

        title_lower = (title or "").lower()
        if any(keyword in title_lower for keyword in self.NOISE_KEYWORDS):
            return  # Filtrage du bruit

        # JSON-LD JobPosting : source structurée, plus fiable que le texte
        # pour la date et l'entreprise. Présent sur toutes les pages testées.
        job_data = {}
        for script_text in response.css('script[type="application/ld+json"]::text').getall():
            try:
                data = json.loads(script_text)
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(data, dict) and data.get("@type") == "JobPosting":
                job_data = data
                break

        # Description complète : "div.PostContent" confirmé sur le vrai HTML
        description_parts = response.css(
            "div.PostContent ::text, div.entry-content ::text, article .content ::text"
        ).getall()
        description = " ".join(p.strip() for p in description_parts if p.strip())

        # Catégorie : "p.PostInfo a" confirmé (breadcrumb réel du site,
        # ex: "Administrateur Base de donnée", "Conseillers / Consultants", "IT")
        category_list = response.css(
            "p.PostInfo a::text, nav.breadcrumb a::text, .breadcrumb a::text, .post-categories a::text"
        ).getall()
        category_list = [c.strip() for c in category_list if c.strip() and c.strip().lower() != "accueil"]
        category = category_list[0] if category_list else None  # None si vraiment rien trouvé, pas de "IT" en dur

        # Région : pattern réel du site "Ville : X" en priorité
        region_match = re.search(
            r"Ville\s*:\s*(.+?)\s*(?:Nom\s*/\s*Entreprise|Email|Tel|Site\s*Web|$)",
            description,
        )
        if region_match:
            region = region_match.group(1).strip()
        else:
            # Repli 1 : autres formulations (Lieu/Région/Pays-Ville)
            alt_match = re.search(
                r"(?:Lieu|Région|Pays\s*/\s*Ville)\s*[:›]?\s*([^\n\r<]+)",
                description, re.IGNORECASE,
            )
            if alt_match:
                region = alt_match.group(1).strip()
            elif job_data.get("jobLocation"):
                # Repli 2 : JSON-LD (attention, parfois imprécis en pratique)
                region = job_data["jobLocation"].get("address", {}).get("addressLocality")
            else:
                region = None  # plus de "Tunisie" en dur : None si vraiment inconnu

        # Date de publication : JSON-LD en priorité (format ISO fiable), puis
        # repli sur le texte si le JSON-LD est absent
        published_date_raw = job_data.get("datePosted")
        if not published_date_raw:
            date_text = response.css("time::text, time::attr(datetime), .entry-date::text, .post-date::text, p.PostDate strong::text").get()
            if not date_text:
                date_match = re.search(
                    r"Publié le\s*([0-9]{1,2}\s+[a-zA-Záàâäãåçéèêëíìîïñóòôöõúùûüýÿæœ]+\s+[0-9]{4})",
                    description, re.IGNORECASE,
                )
                date_text = date_match.group(1) if date_match else None
            published_date_raw = date_text.strip() if date_text else None

        # Entreprise : JSON-LD en priorité, sinon patterns sur le titre
        company = None
        if job_data.get("hiringOrganization"):
            company = job_data["hiringOrganization"].get("name")
        if not company:
            company = self._extract_company(title, description)

        yield {
            "title": title,
            "company": company,
            "url": response.url,
            "category": category,
            "region": region,
            "published_date_raw": published_date_raw,
            "description": description,
            "source": "tunisietravail",
            "market": "tunisia",
        }

    def _extract_company(self, title, description):
        if not title:
            return None

        patterns = [
            r"^(.*?)\s+recrute",
            r"^(.*?)\s+is looking for",
            r"^(.*?)\s+cherche",
            r"^(.*?)\s+offre"
        ]

        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) > 1 and company.lower() not in ["offre", "emploi"]:
                    return company

        # Repli : pattern réel du site "Nom / Entreprise : X"
        comp_match = re.search(r"Nom\s*/\s*Entreprise\s*:\s*([^\n\r]+)", description, re.IGNORECASE)
        if comp_match:
            return comp_match.group(1).strip()

        comp_match = re.search(r"Société\s*:\s*([^\n\r]+)", description, re.IGNORECASE)
        if comp_match:
            return comp_match.group(1).strip()

        return None