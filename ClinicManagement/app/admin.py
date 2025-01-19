from app.models import User, UserRole, MedicineCategory, Medicine
from app import app, db, dao
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import redirect, request, render_template
import json


class AdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class AuthenticatedView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

    @expose('/')
    def index(self):
        return self.render('admin/default.html')


# Logout view
class LogoutView(AuthenticatedView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/login')


# Stats for medicine usage
class stats_medicine(AuthenticatedView):
    @expose('/')
    def index(self):
        stats_medicine_data = dao.stats_by_medic(
            kw=request.args.get('kw'),
            from_date=request.args.get('from_date'),
            to_date=request.args.get('to_date')
        )
        return self.render('admin/stats_medicine.html', statsMedicine=stats_medicine_data)


# Stats for revenue
class stats_revenue(AuthenticatedView):
    @expose('/')
    def index(self):
        stats_revenue_data = dao.stats_by_revenue(month=request.args.get('month'))
        return self.render('admin/stats_revenue.html', statsRevenue=stats_revenue_data)


class MyRuleView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

    @expose('/', methods=['GET', 'POST'])
    def quy_dinh(self):
        err_msg = ""
        quy_dinh = {"tien_kham": 0, "so_benh_nhan": 0}
        try:
            with open("app/data/rules.json", "r") as file:
                quy_dinh = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            err_msg = "Không tìm thấy hoặc lỗi đọc file quy định."

        if request.method == "POST":
            tien_kham = request.form.get("tien_kham", "0")
            so_benh_nhan = request.form.get("so_benh_nhan", "0")

            if not tien_kham.isdigit() or not so_benh_nhan.isdigit():
                err_msg = "Vui lòng nhập số hợp lệ cho tiền khám và số bệnh nhân."
            else:
                tien_kham = int(tien_kham)
                so_benh_nhan = int(so_benh_nhan)
                if tien_kham <= 0 or so_benh_nhan <= 0:
                    err_msg = "Số tiền khám hoặc số bệnh nhân phải lớn hơn 0."
                else:
                    quy_dinh["tien_kham"] = tien_kham
                    quy_dinh["so_benh_nhan"] = so_benh_nhan
                    try:
                        with open("app/data/rules.json", "w") as file:
                            json.dump(quy_dinh, file)
                    except IOError:
                        err_msg = "Không thể ghi dữ liệu vào file."
                    return self.render("admin/rule.html", quy_dinh=quy_dinh, err_msg=err_msg)

        return self.render('admin/rule.html', quy_dinh=quy_dinh, err_msg=err_msg)

class MyAdminView(AdminIndexView):
    @expose('/')
    def index(self):
        statsProduct = dao.count_medicine_by_cate()
        userRoleStats = dao.count_user()
        return self.render('admin/index.html', userRoleStats=userRoleStats, statsProduct=statsProduct)

class UserView(AdminView):
    column_list = ('username', 'email', 'user_role', 'status')
    form_columns = ('username', 'email', 'user_role', 'status')
    column_searchable_list = ['username']
    column_filters = ['id', 'username', 'email']
    can_export = True
    page_size = 10

class MedicineView(AdminView):
    column_list = ('name', 'price', 'unit', 'status', 'category_id', 'description')
    form_columns = ('name', 'price', 'unit', 'status', 'category_id', 'description')
    column_searchable_list = ['name']
    column_filters = ['id', 'name', 'price']
    can_export = True
    page_size = 10

    column_formatters = {
        "price": lambda view, context, model, name: f"{model.price:,.0f} VNĐ"
    }

admin = Admin(app=app, name='QUẢN TRỊ', template_mode='bootstrap4', index_view=MyAdminView())
admin.add_view(UserView(User, db.session, name='Tài khoản'))
admin.add_view(AdminView(MedicineCategory, db.session, name='Danh mục thuốc'))
admin.add_view(MedicineView(Medicine, db.session, name='Danh sách thuốc'))
admin.add_view(MyRuleView(name="Quy định"))
admin.add_view(stats_medicine(name='Thống kê - Báo cáo sử dụng thuốc'))
admin.add_view(stats_revenue(name='Thống kê - Báo cáo doanh thu'))
admin.add_view(LogoutView(name='Đăng xuất'))
