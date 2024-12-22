from statistics import median

from flask import flash, render_template, request, redirect, jsonify, session, url_for
import dao, utils, json
from flask_login import login_user, logout_user, login_required, current_user
from app import login, app, db
from app.models import UserRole

# =============== TEST CONTROLLERS =============== #



# =============== USER CONTROLLERS =============== #
@app.route("/login", methods=['get', 'post'])
def login_process():
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        u = dao.auth_user(username=username, password=password)
        if u:
            login_user(u)
            return redirect('/')
        else:
            return redirect(url_for('login_process'))

    return render_template('login.html')


@app.route("/login-admin", methods=['post'])
def login_admin_process():
    username = request.form.get('username')
    password = request.form.get('password')

    u = dao.auth_user(username=username, password=password, role=UserRole.ADMIN)
    if u:
        login_user(u)

    return redirect('/admin')


@app.route("/profile", methods=['get', 'post'])
@login_required
def profile_process():
    user = current_user
    return render_template('profile.html', user=user)


@app.route("/logout")
def logout_process():
    logout_user()
    return redirect('/login')


@app.route("/register", methods=['GET', 'POST'])
def register_process():
    err_msg = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        name = request.form.get('name')
        birth_day = request.form.get('birth_day')
        address = request.form.get('address')
        telephone = request.form.get('telephone')
        sex = request.form.get('sex')
        avatar = request.files.get('avatar')

        existing_user = dao.get_user_by_username(username)
        if existing_user:
            err_msg = "Tên đăng nhập đã tồn tại. Vui lòng sử dụng tên khác."
        elif password != confirm:
            err_msg = "Mật khẩu và xác nhận mật khẩu KHÔNG khớp."
        elif dao.get_user_by_phone(telephone):
            err_msg = "Số điện thoại đã được sử dụng."
        else:
            import hashlib
            hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()

            avatar_path = None
            if avatar:
                avatar_path = f"static/uploads/{avatar.filename}"
                avatar.save(avatar_path)
            else:
                avatar_path = "static/default-avatar.png"

            try:
                dao.add_user(
                    full_name=name,
                    username=username,
                    password=hashed_password,
                    birth_date=birth_day,
                    gender=int(sex),
                    phone_number=telephone,
                    address=address,
                    avatar=avatar_path,
                    user_role=UserRole.USER,
                    status=True
                )
                return redirect('/login')
            except Exception as e:
                err_msg = f"Đã có lỗi xảy ra: {str(e)}"

    return render_template('register.html', err_msg=err_msg)


@app.route("/change-password", methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    import hashlib
    password_hash = str(hashlib.md5(current_password.encode('utf-8')).hexdigest())

    if current_user.password != password_hash:
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('profile_process'))

    if new_password != confirm_password:
        flash('Mật khẩu mới và xác nhận không giống nhau.', 'danger')
        return redirect(url_for('profile_process'))

    new_password_hash = str(hashlib.md5(new_password.encode('utf-8')).hexdigest())
    if password_hash == new_password_hash:
        flash('New password cannot be the same as the current password.', 'danger')
        return redirect(url_for('profile_process'))

    try:
        current_user.password = str(hashlib.md5(new_password.encode('utf-8')).hexdigest())
        db.session.commit()
        flash('Password updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'danger')

    return redirect(url_for('profile_process'))


@login.user_loader
def get_user_by_id(user_id):
    return dao.get_user_by_id(user_id)


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


# =============== User registers for a medical appointment =============== #
@app.route("/user_dang_ky_kham", methods=['get', 'post'])
def user_dang_ky_kham():
    err_msg = ''
    if request.method == ('POST'):
        with open("app/data/rules.json", "r") as file:
            rules = json.load(file)

            phone_number_input = request.form['user_dang_ky_kham']

            benh_nhan = dao.get_users_by_phone(phone_number_input)
            if benh_nhan and current_user.user_role == UserRole.USER:
                if current_user.id != benh_nhan[0][0]:
                    err_msg = "Bạn không có SDT này hoặc bạn chưa thêm SDT này"
                    return render_template("index.html", err_msg=err_msg)

            if benh_nhan:
                patients_registered_today = dao.load_chi_tiet_danh_sach_kham_today(benh_nhan[0][0])
                if patients_registered_today:
                    err_msg = "Bạn đã đăng ký rồi"
                else:
                    registered_patient_count = dao.get_appointment_counts_for_today()
                    if registered_patient_count:
                        registered_patient_count = registered_patient_count[0][1]
                        max_patient_limit = rules["so_benh_nhan"]
                        if int(registered_patient_count) < int(max_patient_limit):
                            appointment_schedule_today = dao.get_appointments_for_today()
                            if appointment_schedule_today:
                                dao.create_appointment_detail(appointment_schedule_today[0][0], benh_nhan[0][0])
                                err_msg = 'Đăng ký thành công'
                                lsb_for_one_user = dao.load_lich_su_benh(user_id=benh_nhan[0][0])
                                if lsb_for_one_user:
                                    pass
                                else:
                                    dao.add_medical_history(user_id=benh_nhan[0][0])
                            else:
                                err_msg = "Chưa có danh sách để đăng ký"
                        else:
                            err_msg = "Số lượng bệnh nhân trong danh sách đã đầy, vui lòng đăng ký khám vào hôm sau"
                    else:
                        registered_patient_count = 0
                        if registered_patient_count == 0:
                            max_patient_limit = rules["so_benh_nhan"]
                            if registered_patient_count < int(max_patient_limit):
                                appointment_schedule_today = dao.get_appointments_for_today()
                                if appointment_schedule_today:
                                    dao.create_appointment_detail(appointment_schedule_today[0][0], benh_nhan[0][0])
                                    err_msg = 'Đăng ký thành công'
                                    lsb_for_one_user = dao.load_lich_su_benh(user_id=benh_nhan[0][0])
                                    if lsb_for_one_user:
                                        pass
                                    else:
                                        dao.add_medical_history(user_id=benh_nhan[0][0])
                                else:
                                    err_msg = "Chưa có danh sách để đăng ký"
                            else:
                                err_msg = "Có lỗi xảy ra"
                        else:
                            err_msg = "Có lỗi xảy ra"

            else:
                err_msg = "Không tồn tại user trong cơ sở dữ liệu"

    return render_template("index.html", err_msg=err_msg)


# =============== Create appointment =============== #
@app.route("/create_danh_sach_kham_for_nurse", methods=['get', 'post'])
def create_danh_sach_kham_for_nurse():
    err_msg = ''
    if request.method == ('POST'):

        danh_sach_kham_hom_nay = dao.get_appointments_for_today()
        if danh_sach_kham_hom_nay:
            err_msg = "Đã tạo danh sách khám cho hôm nay rồi"
        else:
            create_list = request.form['create_list']
            dao.create_danh_sach_kham(create_list)
            ma_phieu_kham_today = dao.get_newest_appoinment_id()
            return redirect('/nurse')
    return render_template("nurse.html", err_msg=err_msg)


@app.route("/save_chi_tiet_danh_sach_kham", methods=['get', 'post'])
def save_chi_tiet_danh_sach_kham():
    err_msg = ''
    if request.method == ('POST'):
        dsk = dao.load_DSK_today()
        if dsk:
            chi_tiet_dsk = dao.load_chi_tiet_DSK_today(dsk[0][0])
            if chi_tiet_dsk:
                n = len(chi_tiet_dsk)
                for i in range(0, n):
                    pk_today_for_one_user = dao.get_prescriptions_for_today(user_id=chi_tiet_dsk[i][2])
                    if pk_today_for_one_user:
                        err_msg = "Đã tạo phiếu cho user này rồi"
                    else:
                        pk = dao.create_phieu_kham_auto(user_id=chi_tiet_dsk[i][2])
                        err_msg = "Tạo thành công phiếu khám"
            else:
                err_msg = "Chưa có bệnh nhân nào đăng ký khám"

        save_chi_tiet_dsk = request.form['save_chi_tiet_dsk']

    return render_template("nurse.html", err_msg=err_msg)


# =============== Create prescription =============== #
@app.route("/doctor_get_user_by_user_id", methods=['get', 'post'])
def doctor_get_user_by_user_id():
    err_msg = ''
    if request.method == ('POST'):
        user_id = request.form["doctor_get_user_by_user_id"]
        action = request.form.get('action')
        phieu_kham_da_duoc_tao = dao.get_prescriptions_for_today(user_id)
        if phieu_kham_da_duoc_tao:
            pk_today_for_one_user = dao.load_phieu_kham_today_by_user_id(user_id)
            global ma_phieu_kham_today
            ma_phieu_kham_today = pk_today_for_one_user[0][0]
            if pk_today_for_one_user:
                global user_id_in_phieu_kham
                user_id_in_phieu_kham = pk_today_for_one_user[0][5]
                user_in_phieu_kham = dao.load_users_by_user_id(user_id_in_phieu_kham)
                # LƯU THUỐC CHO BỆNH NHÂN
                if user_in_phieu_kham:
                    ten_thuoc = request.form["medicine"]
                    so_luong_thuoc = request.form["so_luong_thuoc"]
                    thuoc = dao.load_medicines_by_name(ten_thuoc)
                    if thuoc:
                        dao.save_chi_tiet_phieu_kham(so_luong_thuoc=so_luong_thuoc, thuoc_id=thuoc[0][0],
                                                     phieu_kham_id=pk_today_for_one_user[0][0])

                        return render_template("doctor.html", err_msg=err_msg, tmp=user_id)
                    else:
                        err_msg = "Không có thuốc này trong cơ sở dữ liệu"
                else:
                    err_msg = "Bệnh nhân này không có phiếu khám"
            else:
                err_msg = "Không tìm được mã bệnh nhân trong danh sách các phiếu khám"
        else:
            err_msg = "Phiếu khám chưa được tạo"
    return render_template("doctor.html", err_msg=err_msg)


user_id_in_phieu_kham = 0
ma_phieu_kham_today = 0


@app.context_processor
def load_users_by_user_id_view():
    user_id_view = dao.load_users_by_user_id(user_id_in_phieu_kham)
    return {
        "user_id_view": user_id_view
    }


@app.context_processor
def load_prescription_details_today():
    prescription_details_today = dao.load_prescription_details_today(ma_phieu_kham_today)
    return {
        "prescription_details_today": prescription_details_today
    }


@app.context_processor
def load_thuoc_trong_chi_tiet_pk():
    thuoc_trong_ctpk = dao.load_thuoc_in_chi_tiet_phieu_kham_today(
        user_id_in_phieu_kham)
    return {
        'thuoc_trong_ctpk': thuoc_trong_ctpk
    }


@app.route("/doctor_save_phieu_kham", methods=['get', 'post'])
def doctor_save_phieu_kham():
    err_msg = ''
    if request.method == ('POST'):
        phieu_kham_id = ma_phieu_kham_today
        check_pk_id = dao.load_phieu_kham_id_today_by_phieu_kham_id(phieu_kham_id=phieu_kham_id)

        if check_pk_id:
            check_pk_id_numString = str(check_pk_id[0][0])
            trieu_chung = request.form.get("trieu_chung")
            chuan_doan = request.form.get("chuan_doan")
            if trieu_chung and chuan_doan:
                dao.update_phieu_kham(phieu_kham_id=check_pk_id_numString, trieu_chung=trieu_chung,
                                      chuan_doan=chuan_doan)
                benh_id = dao.load_benh_id_by_ten_benh(chuan_doan)
                lsb_id = dao.load_lich_su_benh_id_by_phieu_kham_id(check_pk_id_numString)

                dao.save_chi_tiet_lich_su_benh(lich_su_benh_id=lsb_id[0][0], benh_id=benh_id[0][0])
                err_msg = "Lưu thành công phiếu khám có mã phiếu là " + check_pk_id_numString
            else:
                err_msg = "Chưa nhập chuẩn đoán và triệu chứng"
        else:
            err_msg = "Không tồn tại phiếu khám này"
    return render_template("doctor.html", err_msg=err_msg)

# =============== Payment =============== #
@app.route("/cashier", methods=['get', 'post'])
def cashier():
    err_msg = ''
    hd = ""
    if request.method == ('POST'):
        with open("app/data/rules.json", "r") as file:
            rules = json.load(file)
        tien_kham = rules["tien_kham"]
        phieuKham_id = request.form['submit_phieuKham_id']
        check_pk_id = dao.load_phieu_kham_id_today_by_phieu_kham_id(phieu_kham_id=phieuKham_id)
        if check_pk_id:
            global user_id_in_hoa_don_for_one_user
            user_id_in_hoa_don_for_one_user = phieuKham_id
            phieu_kham = dao.get_prescription_details(phieuKham_id)
            bill_cua_user = dao.bill_for_one_user_by_id(phieu_kham[0][5])
            tien_kham = float(tien_kham)
            if bill_cua_user and tien_kham >= 0 and not dao.check_payment_status(bill_cua_user[0]):
                tien_thuoc = bill_cua_user[4] + tien_kham
                dao.save_bill_for_user(phieu_kham[0][2], tien_thuoc, phieu_kham[0][5])
                dao.payment(bill_cua_user[0])
                err_msg = "Thanh toán thành công"
                return render_template("cashier.html", err_msg=err_msg, tien_kham=tien_kham)
            else:
                tien_kham = 0
                err_msg = "Chưa có hóa đơn"
                return render_template("cashier.html", err_msg=err_msg, tien_kham=tien_kham)
        else:
            err_msg = "Không tồn tại phiếu khám này trong ngày hôm nay"
        return render_template("cashier.html", err_msg=err_msg)

    return render_template("cashier.html", err_msg=err_msg)

user_id_in_hoa_don_for_one_user = 0


@app.context_processor
def common_attribute():
    categories = dao.load_categories()
    return {
        'categories': categories,
        'cart': utils.cart_stats(session.get(app.config['CART_KEY']))
    }


@app.context_processor
def get_disease():
    diseases = dao.load_diseases()
    return {
        'diseases': diseases
    }


@app.context_processor
def get_danh_sach_kham():
    danh_sach_kham = dao.load_danh_sach_kham()
    return {
        'danh_sach_kham': danh_sach_kham
    }


@app.context_processor
def get_user_in_danh_sach_kham():
    get_user_in_danh_sach_kham = dao.get_user_in_danh_sach_kham()
    return {
        'get_user_in_danh_sach_kham': get_user_in_danh_sach_kham
    }


@app.context_processor
def get_user_in_danh_sach_kham():
    get_user_in_danh_sach_kham = []
    dsk = dao.load_DSK_today()
    if dsk:
        user_id_in_dsk = dao.load_chi_tiet_DSK_today(dsk[0][0])
        n = len(user_id_in_dsk)

        for i in range(0, n):
            get_user_in_danh_sach_kham.append(dao.load_users_by_user_id(user_id_in_dsk[i][2]))

    return {
        'get_user_in_danh_sach_kham': get_user_in_danh_sach_kham
    }


@app.context_processor
def load_hoa_don():
    danh_sach_hoa_don = dao.load_hoa_don()
    return {
        "danh_sach_hoa_don": danh_sach_hoa_don
    }


@app.context_processor
def load_hoa_don_for_one_user():
    hoa_don = dao.load_hoa_don_by_phieu_kham_id(
        user_id_in_hoa_don_for_one_user)
    return {
        "hoa_don": hoa_don
    }

# =============== Medical history =============== #

user_id_in_lich_su_benh_after_filter = 0


@app.route("/lay_ma_benh_nhan_xem_lich_su_benh", methods=['GET', 'POST'])
def lay_ma_benh_nhan_xem_lich_su_benh():
    err_msg = ''
    medical_history = None
    lsb = None
    if request.method == 'POST':
        id_benh_nhan = request.form.get("id_benh_nhan")

        if not id_benh_nhan:
            err_msg = "Vui lòng nhập mã bệnh nhân"
        else:
            try:
                medical_history = dao.load_prescription_data(id_benh_nhan)
                lsb = dao.load_lich_su_benh_in_view(id_benh_nhan)
                if not lsb:
                    err_msg = "Không tồn tại bệnh nhân này"
            except Exception as e:
                err_msg = f"Lỗi xảy ra: {str(e)}"
    else:
        err_msg = "Vui lòng nhập để tìm kiếm lịch sử bệnh"
    # print("debug /lay_ma_benh_nhan_xem_lich_su_benh:")
    # for i in lsb:
    #     print(i)
    # for i in medical_history:
    #     print(i)
    return render_template("medical_history.html",
                           err_msg=err_msg,
                           prescription=medical_history,
                           load_lich_su_benh_in_view=lsb)

@app.route("/medical_history")
def lich_su_benh():
    print("debugg /lich_su_benh:")
    if current_user.is_authenticated:
        lsb_for_crr = dao.load_lich_su_benh_in_view()
    all_users = dao.load_users()
    all_prescriptions = []
    all_medical_history = []
    for user in all_users:
        user_prescription_data = dao.load_prescription_data(user.id)
        if user_prescription_data:
            all_prescriptions.append({"user": user, "prescription": user_prescription_data})

    for i in all_prescriptions:
        for j in i['prescription']:
            all_medical_history.append(j)
    for i in lsb_for_crr:
        print(i)
    for i in all_medical_history:
        print(i)
    return render_template("medical_history.html", load_lich_su_benh_in_view=lsb_for_crr, all_medical_history=all_medical_history)



# =============== API =============== #
@app.route('/api/users', methods=['GET'])
def get_all_users():
    users = dao.load_users()
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "full_name": user.full_name,
            "username": user.username,
            "phone_number": user.phone_number,
            "address": user.address,
            "gender": user.gender,
            "birth_date": user.birth_date,
            "avatar": user.avatar
        })
    return jsonify(user_list)