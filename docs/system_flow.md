# System Flow

The typical runtime flow follows a linear path:

1. Camera captures frame → 2. Recognition engine analyzes frame →
3. Attendance service updates record → 4. Data persisted (CSV/DB) →
5. Web dashboard queries storage to display current state.

Additional subflows include mobile attendance (image upload), voice
verification, and crowd analytics, but the core path remains the same.