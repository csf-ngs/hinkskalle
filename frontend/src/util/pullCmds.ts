import { getEnv } from './env';

export function pullCmd(manifest: { type: string; path: string }, tag: string): string {
  let backend = (getEnv('VUE_APP_BACKEND_URL') as string).replace(/^https?:\/\//, '');
  if (!backend.endsWith('/')) {
    backend += '/';
  }
  const hasHttps = (getEnv('VUE_APP_BACKEND_URL') as string).startsWith('https');
  let singularityCmdEnv = getEnv('VUE_APP_SINGULARITY_COMMAND');
  if (singularityCmdEnv == "") {
    singularityCmdEnv = "singularity"; 
  } 
  switch(manifest.type) {
    case('singularity'):
      return `${singularityCmd} pull oras://${backend}${manifest.path}:${tag}`
    case('docker'):
    case('oci'):
      return `docker pull ${backend}${manifest.path}:${tag}`
    case('oras'):
      return `oras pull ${hasHttps ? '' : '--plain-http '}${backend}${manifest.path}:${tag}`
    default:
      return `curl something`
  }
}

export function libraryUrl(image: { path: string}, tag: string) {
  return `${image.path}:${tag}`
}

export function singularityCmd(): string {
  let singularityCmdEnv = getEnv('VUE_APP_SINGULARITY_COMMAND');
  if (singularityCmdEnv == "") {
    singularityCmdEnv = "singularity"; 
  } 
  return `${singularityCmdEnv}`; 
}	
