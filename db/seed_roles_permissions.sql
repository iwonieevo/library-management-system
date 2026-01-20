-- ROLES
INSERT INTO app_role (name, description) VALUES
  ('superadmin', 'Full system access'),
  ('admin', 'Administrative access'),
  ('librarian', 'Library operations'),
  ('member', 'Library member')
ON CONFLICT (name) DO NOTHING;

-- PERMISSIONS
INSERT INTO entity_permission (name, entity, access_level) VALUES
  ('superadmin panel read', 'superadmin_panel', 'read'),
  ('books read-only', 'book', 'read'),
  ('books create', 'book', 'create'),
  ('books update', 'book', 'update'),
  ('books delete', 'book', 'delete')
ON CONFLICT (name) DO NOTHING;

-- ROLES PERMISSIONS
INSERT INTO app_role_entity_permission (role_id, permission_id)
VALUES
  (get_role_id('superadmin'), get_permission_id('superadmin panel read')),
  (get_role_id('admin'), get_permission_id('books update')),
  (get_role_id('librarian'), get_permission_id('books create')),
  (get_role_id('member'), get_permission_id('books read-only'))
ON CONFLICT DO NOTHING;