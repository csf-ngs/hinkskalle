export function getEnv(name: string): string | boolean {
  return (window as any)?.configs?.[name] || process.env[name]
}