export function icon(name, className = '') {
  return `<svg class="icon ${className}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><use href="icons.svg#${name}"></use></svg>`;
}
export function buttonContent(name, label) {
  return `${icon(name)}<span class="button-label">${label}</span>`;
}
