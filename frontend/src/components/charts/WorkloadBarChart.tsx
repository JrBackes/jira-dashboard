import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export function WorkloadBarChart({ data }: { data: Record<string, number> }) {
  const chartData = Object.entries(data).map(([statusCategory, count]) => ({ statusCategory, count }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={chartData}>
        <XAxis dataKey="statusCategory" />
        <YAxis allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="count" name="Itens" fill="#4f46e5" />
      </BarChart>
    </ResponsiveContainer>
  );
}
