import { SectionCard } from '../../components/common/SectionCard';
import { Badge } from '../../components/common/Badge';

interface PlaceholderPageProps {
  title: string;
  description: string;
}

export default function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <SectionCard title={title} subtitle="Planned route" action={<Badge label="Stub" tone="neutral" />}>
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white/40 p-12 text-center text-slate-400">
        {description}
      </div>
    </SectionCard>
  );
}
