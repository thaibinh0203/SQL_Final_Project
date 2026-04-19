Cloud import order for managed MySQL services such as Railway:

1. `cloud_01_schema.sql`
2. `cloud_seed_510.sql`
3. `cloud_02_views.sql`
4. `cloud_03_routines.sql`
5. `cloud_04_triggers.sql`

Notes:
- These files intentionally remove `CREATE DATABASE` and `USE recruitment_management_system;`.
- Connect directly to the target database before running them.
- `05_security.sql` is usually not needed on managed cloud MySQL and may fail depending on provider permissions.
