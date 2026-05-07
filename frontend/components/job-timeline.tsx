import type { JobTimelineItem } from "@/lib/types";

export function JobTimeline({ items }: { items: JobTimelineItem[] }) {
  return (
    <ol className="timeline" aria-label="Job processing timeline">
      {items.map((item) => (
        <li key={item.stage} className={`timeline__item timeline__item--${item.state}`}>
          <span className="timeline__marker" aria-hidden="true" />
          <div>
            <p className="timeline__label">{item.label}</p>
            <p className="timeline__state">{item.state}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
