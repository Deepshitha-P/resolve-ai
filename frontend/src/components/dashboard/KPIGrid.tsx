import { KPIStatCard } from '../common/KPIStatCard';
import type { DashboardKpi } from '../../types/api';

interface KPIGridProps {
  items: DashboardKpi[];
}

export function KPIGrid({ items }: KPIGridProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <KPIStatCard key={item.label} {...item} />
      ))}
    </div>
  );
}
