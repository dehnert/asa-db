import sys

def migrate_perms_forwards(orm, perms, ):
    for app_name, model_name, codename, verbose_name in perms:
        ct, created = orm['contenttypes.ContentType'].objects.get_or_create(model=model_name, app_label=app_name) # model must be lowercase!
        perm, created = orm['auth.permission'].objects.get_or_create(
            content_type=ct,
            codename=codename,
            defaults={'name':verbose_name},
        )

def migrate_perms_backwards(orm, perms, ):
    for app_name, model_name, codename, verbose_name in perms:
        try:
            ct = orm['contenttypes.ContentType'].objects.get(model=model_name, app_label=app_name) # model must be lowercase!
            orm['auth.permission'].objects.get(
                content_type=ct,
                codename=codename,
            ).delete()
        except orm['contenttypes.ContentType'].DoesNotExist:
            print >>sys.stderr, "ContentType %s.%s does not exist while backwards migrating adding the %s permission on it." % (app_name, model_name, codename, )
        except orm['auth.permission'].DoesNotExist:
            print >>sys.stderr, "Permission %s does not exist on content type %s (%s.%s) while backwards migrating its addition." % (codename, ct, app_name, model_name, )
            

def migrate_groups_forwards(orm, groups, ):
    for group_name, perms in groups:
        group_obj, created = orm['auth.Group'].objects.get_or_create(name=group_name)
        for app_name, model_name, codename in perms:
            try:
                ct = orm['contenttypes.ContentType'].objects.get(model=model_name, app_label=app_name)
                group_obj.permissions.add(orm['auth.permission'].objects.get(
                    content_type=ct,
                    codename=codename,
                ))
            except orm['contenttypes.ContentType'].DoesNotExist:
                print >>sys.stderr, "ContentType %s.%s does not exist while adding %s permission to %s group." % (app_name, model_name, codename, group_name, )
                raise
            except orm['auth.permission'].DoesNotExist:
                print >>sys.stderr, "Permission %s does not exist on content type %s (%s.%s) while adding it to group %s." % (codename, ct, app_name, model_name, group_name, )
                raise
        group_obj.save()

def migrate_groups_backwards(orm, groups, ):
    for group_name, perms in groups:
        try:
            orm['auth.Group'].objects.get(name=group_name).delete()
        except orm['auth.Group'].DoesNotExist:
            print >>sys.stderr, "Group %s does not exist while backwards migrating its addition." % (group_name, )
