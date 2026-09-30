import json


class JsonWriterPipeline:
    def open_spider(self, spider):
        filename = f"{spider.name}_output.jsonl"
        self.file = open(filename, "w", encoding="utf-8")

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item