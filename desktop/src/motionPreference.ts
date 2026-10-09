// Subscribe to the OS preference while the desk stays open, not only on startup.
export function observeReducedMotion(update:(reduced:boolean)=>void) {
  const preference=matchMedia('(prefers-reduced-motion: reduce)');
  const changed=()=>update(preference.matches);
  changed();preference.addEventListener('change',changed);
  return ()=>preference.removeEventListener('change',changed);
}
