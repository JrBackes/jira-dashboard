import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export function WorkloadBarChart({ data }: { data: Record<string, number> }) {
  const chartData = Object.entries(data).map(([status, count]) => ({ status, count }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={chartData}>
        <XAxis dataKey="status" angle={-20} textAnchor="end" height={60} interval={0} />
        <YAxis allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="count" name="Itens" fill="#4f46e5" />
      </BarChart>
    </ResponsiveContainer>
  );
}
