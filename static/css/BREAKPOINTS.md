# CSS Breakpoints Documentation

## Overview
This document outlines the responsive breakpoints used throughout the Shuttrly application's CSS system.

## Breakpoint System

### Mobile & Tablet
- **Range**: `max-width: 1099px`
- **Usage**: Mobile phones and small tablets
- **Layout**: Single column, mobile-optimized interface

### Desktop Small
- **Range**: `min-width: 1025px and max-width: 1199px`
- **Usage**: Small desktop screens and large tablets
- **Layout**: Two-column layout with reduced sidebar

### Desktop Medium
- **Range**: `min-width: 1200px and max-width: 1499px`
- **Usage**: Standard desktop screens
- **Layout**: Full three-column layout

### Desktop Large
- **Range**: `min-width: 1651px and max-width: 1999px`
- **Usage**: Large desktop screens
- **Layout**: Optimized for larger displays

### Ultra-wide
- **Range**: `min-width: 2000px`
- **Usage**: Ultra-wide monitors and large displays
- **Layout**: Maximum spacing and sizing

## Special Breakpoints

### Extra Small Mobile
- **Range**: `max-width: 480px`
- **Usage**: Very small mobile devices
- **Features**: Compact layout, smaller fonts

### Landscape Mobile
- **Range**: `max-width: 768px and orientation: landscape`
- **Usage**: Mobile devices in landscape mode
- **Features**: Horizontal layout optimization

## Implementation Notes

- All breakpoints use pixel values for consistency
- No `calc()` functions in media queries for better performance
- Breakpoints are defined in `base.scss` and used across all component files
- Variables are used for consistent spacing and sizing within each breakpoint

## Usage Example

```scss
/* Mobile and Tablet */
@media (max-width: 1024px) {
  .component {
    width: 100%;
    padding: 1rem;
  }
}

/* Desktop */
@media (min-width: 1025px) {
  .component {
    width: 50%;
    padding: 2rem;
  }
}
```

---
*Last updated: January 2025*
