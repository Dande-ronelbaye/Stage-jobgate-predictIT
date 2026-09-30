import { Plus, X } from "lucide-react";
import { KeyboardEvent, useState } from "react";

interface Props {
  tags: string[];
  onChange: (tags: string[]) => void;
  suggestions?: string[];
}

export function TagInput({ tags, onChange, suggestions = [] }: Props) {
  const [value, setValue] = useState("");

  const addTag = (raw: string) => {
    const t = raw.trim().replace(/,+$/, "");
    if (!t) return;
    if (tags.some((x) => x.toLowerCase() === t.toLowerCase())) return;
    onChange([...tags, t]);
    setValue("");
  };

  const removeTag = (t: string) => onChange(tags.filter((x) => x !== t));

  const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag(value);
    } else if (e.key === "Backspace" && !value && tags.length) {
      removeTag(tags[tags.length - 1]);
    }
  };

  const remainingSuggestions = suggestions.filter(
    (s) => !tags.some((t) => t.toLowerCase() === s.toLowerCase()),
  );

  return (
    <div className="space-y-3">
      <div className="glass-inset group flex min-h-[52px] flex-wrap items-center gap-2 rounded-xl px-3 py-2 transition-all focus-within:ring-2 focus-within:ring-primary/60">
        {tags.map((tag, i) => (
          <span
            key={tag}
            style={{ animationDelay: `${i * 40}ms` }}
            className="animate-scale-in inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-indigo-500/90 to-violet-500/90 px-3 py-1 text-xs font-semibold text-white shadow-sm shadow-violet-500/30"
          >
            {tag}
            <button
              type="button"
              onClick={() => removeTag(tag)}
              className="rounded-full p-0.5 transition-colors hover:bg-white/25"
              aria-label={`Remove ${tag}`}
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKey}
          onBlur={() => value && addTag(value)}
          placeholder={tags.length ? "" : "React, Python, Docker…"}
          className="min-w-[120px] flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
      </div>

      {remainingSuggestions.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          <span className="text-[11px] uppercase tracking-wider text-muted-foreground">Quick add</span>
          {remainingSuggestions.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => addTag(s)}
              className="group inline-flex items-center gap-1 rounded-full border border-border bg-background/50 px-2.5 py-0.5 text-xs text-muted-foreground transition-all hover:border-primary/50 hover:bg-primary/10 hover:text-foreground"
            >
              <Plus className="h-3 w-3 opacity-60 group-hover:opacity-100" />
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
