import { Bar, BarChart, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { VelocityPoint } from '../../api/sprints';

export function VelocityChart({ data }: { data: VelocityPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data}>
        <XAxis dataKey="sprint_name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="planned_points" name="Planejado" fill="#94a3b8" />
        <Bar dataKey="delivered_points" name="Entregue" fill="#4f46e5" />
      </BarChart>
    </ResponsiveContainer>
  );
}
