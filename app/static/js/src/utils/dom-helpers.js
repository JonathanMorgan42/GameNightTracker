/**
 * DOM manipulation helper utilities
 */

/**
 * Query selector with error handling
 */
export function $(selector, parent = document) {
  return parent.querySelector(selector);
}

/**
 * Query selector all
 */
export function $$(selector, parent = document) {
  return Array.from(parent.querySelectorAll(selector));
}

/**
 * Add event listener with automatic cleanup
 */
export function on(element, event, handler, options) {
  if (!element) return () => {};

  element.addEventListener(event, handler, options);

  // Return cleanup function
  return () => {
    element.removeEventListener(event, handler, options);
  };
}

/**
 * Toggle class on element
 */
export function toggleClass(element, className, force) {
  if (!element) return;
  element.classList.toggle(className, force);
}

/**
 * Add class to element
 */
export function addClass(element, ...classNames) {
  if (!element) return;
  element.classList.add(...classNames);
}

/**
 * Remove class from element
 */
export function removeClass(element, ...classNames) {
  if (!element) return;
  element.classList.remove(...classNames);
}

/**
 * Check if element has class
 */
export function hasClass(element, className) {
  if (!element) return false;
  return element.classList.contains(className);
}

/**
 * Set multiple attributes
 */
export function setAttributes(element, attrs) {
  if (!element) return;

  Object.entries(attrs).forEach(([key, value]) => {
    if (value === null || value === undefined) {
      element.removeAttribute(key);
    } else {
      element.setAttribute(key, value);
    }
  });
}

/**
 * Create element with attributes and children
 */
export function createElement(tag, attrs = {}, children = []) {
  const element = document.createElement(tag);

  // Set attributes
  setAttributes(element, attrs);

  // Add children
  children.forEach(child => {
    if (typeof child === 'string') {
      element.appendChild(document.createTextNode(child));
    } else if (child instanceof Node) {
      element.appendChild(child);
    }
  });

  return element;
}

/**
 * Remove all children from element
 */
export function removeAllChildren(element) {
  if (!element) return;

  while (element.firstChild) {
    element.removeChild(element.firstChild);
  }
}

/**
 * Show element
 */
export function show(element) {
  if (!element) return;
  element.style.display = '';
  removeClass(element, 'display-none', 'hidden');
}

/**
 * Hide element
 */
export function hide(element) {
  if (!element) return;
  addClass(element, 'display-none');
}

/**
 * Check if element is visible
 */
export function isVisible(element) {
  if (!element) return false;
  return element.offsetParent !== null;
}

/**
 * Smoothly scroll element into view
 */
export function scrollIntoView(element, options = {}) {
  if (!element) return;

  element.scrollIntoView({
    behavior: 'smooth',
    block: 'center',
    ...options,
  });
}

/**
 * Wait for element to be available in DOM
 */
export function waitForElement(selector, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const element = $(selector);
    if (element) {
      resolve(element);
      return;
    }

    const observer = new MutationObserver(() => {
      const element = $(selector);
      if (element) {
        observer.disconnect();
        resolve(element);
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    setTimeout(() => {
      observer.disconnect();
      reject(new Error(`Element ${selector} not found within ${timeout}ms`));
    }, timeout);
  });
}
