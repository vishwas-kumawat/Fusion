from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, DepartmentInfo, Designation, HoldsDesignation

try:
    user = User.objects.get(username='admin')
    dept, _ = DepartmentInfo.objects.get_or_create(name='Computer Science and Engineering')
    ExtraInfo.objects.get_or_create(user=user, id=user.username, defaults={'user_type': 'staff', 'department': dept})
    desig, _ = Designation.objects.get_or_create(name='admin')
    HoldsDesignation.objects.get_or_create(user=user, working=user, designation=desig)
    print('========== SUCCESS! admin user configured successfully! ==========')
except Exception as e:
    print(f'========== ERROR: {e} ==========')
