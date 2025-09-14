# Follow/Unfollow Buttons Integration

## Overview
This document describes the integration of follow/unfollow buttons in the social stats modals, ensuring consistency with the sidebar recommendations system.

## CSS Classes

### Primary Button Class
```css
.follow-btn
```
- **Usage**: Main class for all follow/unfollow buttons
- **Location**: Used in both sidebar recommendations and modal lists
- **Styling**: Inherits from base button styles with primary color scheme

### State Classes
```css
.follow-btn.following
```
- **Usage**: Applied when user is currently following the target user
- **Visual**: Different background color to indicate active following state

## HTML Structure

### Modal Button Template
```html
<button class="follow-btn" 
        data-user-id="{{ user.id }}" 
        data-username="{{ user.username }}"
        data-action="follow"
        onclick="event.preventDefault(); window.recommendationsManager.followUser({{ user.id }}, '{{ user.username }}')">
    Follow
</button>
```

### Following State Button
```html
<button class="follow-btn following" 
        data-user-id="{{ user.id }}" 
        data-username="{{ user.username }}"
        data-action="unfollow"
        onclick="event.preventDefault(); window.recommendationsManager.followUser({{ user.id }}, '{{ user.username }}')">
    Unfollow
</button>
```

## JavaScript Integration

### Event Binding
The buttons use the same `RecommendationsManager` class as the sidebar:
- **Function**: `window.recommendationsManager.followUser(userId, username)`
- **Behavior**: Toggles follow/unfollow state
- **Feedback**: Shows loading spinner and success animations

### Dynamic Text Updates
- **Follow Action**: Button text changes to "Unfollow" after successful follow
- **Unfollow Action**: Button text changes to "Follow" after successful unfollow
- **Loading States**: Shows "Following..." or "Unfollowing..." during API calls

## Data Attributes

| Attribute | Purpose | Values |
|-----------|---------|--------|
| `data-user-id` | Target user ID for API calls | Integer |
| `data-username` | Target username for API calls | String |
| `data-action` | Current button action | "follow" or "unfollow" |

## Animation States

### CSS Classes Applied During Actions
- `.btn-animating` - Initial click animation
- `.btn-success` - Success state with checkmark
- `.btn-pulse` - Success pulse animation
- `.btn-error` - Error state with shake animation

### Loading States
- **Follow**: "Following..." with spinner
- **Unfollow**: "Unfollowing..." with spinner

## Integration Points

### Templates
- `followers_list.html` - Followers modal content
- `following_list.html` - Following modal content
- `recommendations_list.html` - Sidebar recommendations

### JavaScript Files
- `recommendations.js` - Main follow/unfollow logic
- `own_profile.html` - Modal event binding

### CSS Files
- `base.scss` - Core button styles
- `users.scss` - Modal-specific styles

## Usage Examples

### Adding Follow Button to New Modal
```html
<button class="follow-btn" 
        data-user-id="123" 
        data-username="example_user"
        data-action="follow"
        onclick="event.preventDefault(); window.recommendationsManager.followUser(123, 'example_user')">
    Follow
</button>
```

### Checking Follow State
```javascript
const button = document.querySelector('.follow-btn[data-user-id="123"]');
const isFollowing = button.classList.contains('following');
const action = button.getAttribute('data-action');
```

## Notes
- All buttons use the same API endpoint: `/ajax/toggle-follow/`
- CSRF token is automatically handled by the RecommendationsManager
- Toast notifications are shown for success/error states
- Buttons are automatically re-enabled after actions complete
