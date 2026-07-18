// O Jira só tem 3 categorias fixas de status (statusCategory.key, estável e em inglês),
// independente de quantos status customizados um projeto tenha. Aqui só traduzimos
// para exibição — a API continua retornando as chaves originais.
const STATUS_CATEGORY_LABELS: Record<string, string> = {
  new: 'A Fazer',
  indeterminate: 'Em Andamento',
  done: 'Concluído',
};

export function statusCategoryLabel(key: string): string {
  return STATUS_CATEGORY_LABELS[key] ?? key;
}
