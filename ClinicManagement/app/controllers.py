from datetime import datetime, timedelta

from flask import flash, render_template, request, redirect, jsonify, session, url_for, sessions
import dao, utils, json
from flask_login import login_user, logout_user, login_required, current_user
from app import login, app, db
from app.models import UserRole
import cloudinary
import cloudinary.uploader

# =============== TEST CONTROLLERS =============== #






# =============== USER CONTROLLERS =============== #
# Các thao tác của USER:
# - Đăng nhập: nếu status của User là false sẽ không đăng nhập được
# - Đăng ký
# - Đăng xuất
# - Cập nhật thông tin người dùng: hình ảnh, mật khẩu, họ tên,....


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


@app.route('/update-profile', methods=['POST'])
def update_profile_process():
    if not current_user.is_authenticated:
        return redirect(url_for('login_process'))

    full_name = request.form.get('name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    avatar = request.files.get('avatar')
    avatar_path = None
    if avatar:
        res = cloudinary.uploader.upload(avatar)
        avatar_path = res['secure_url']
    try:
        user_updated = dao.update_user(user_id=current_user.id, full_name=full_name,
                                       phone_number=phone, address=address, avatar=avatar_path)
        if user_updated:
            flash('Đã lưu thông tin thông tin thành công!', 'success')
        else:
            flash('Không thể lưu thông tin!', 'danger')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')

    return redirect(url_for('profile_process'))


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
        gender = request.form.get('sex')
        avatar = request.files.get('avatar')

        existing_user = dao.get_user_by_username(username=username)
        if existing_user:
            err_msg = "Tên đăng nhập đã tồn tại. Vui lòng sử dụng tên khác."
        elif password != confirm:
            err_msg = "Mật khẩu và xác nhận mật khẩu KHÔNG khớp."
        elif dao.get_user_by_phone(phone_number=telephone):
            err_msg = "Số điện thoại đã được sử dụng."
        else:
            import hashlib
            hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()

            avatar_path = None
            if avatar:
                res = cloudinary.uploader.upload(avatar)
                avatar_path = res['secure_url']
            try:
                dao.add_user(
                    full_name=name,
                    username=username,
                    password=hashed_password,
                    birth_date=birth_day,
                    gender=int(gender),
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


# ============================== USER REGISTER APPOINTMENT ============================== #
# Thao tác đăng ký khám bệnh của người dùng
# Bao gồm các chức năng:
# - Chọn ngày và giờ để đăng ký
# - Hệ thống tự động kiểm tra danh sách đã đủ hay chưa
# - Hệ thống tự động kiểm tra thông tin của User và chỉ cho User đăng ký bằng SDT của mình
# - Hệ thống tự động tạo AppointmentList mới trong trường hợp chưa có
# - Trường hợp đặc biệt là Admin và Nurse sẽ có quyền đăng ký bất kỳ số điện thoại nào trong hệ thống


@app.route("/appointment_register", methods=['GET'])
@login_required
def appointment_register_process():
    return render_template('appointment_register.html')


@app.route("/user_dang_ky_kham", methods=['GET', 'POST'])
def user_dang_ky_kham():
    err_msg = ''
    suc_msg = ''
    if request.method == 'POST':
        with open("app/data/rules.json", "r") as file:
            rules = json.load(file)

        phone_number_input = request.form['user_dang_ky_kham']
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']

        max_patient_limit = int(rules.get("so_benh_nhan", 0))

        patient = dao.get_user_by_phone(phone_number=phone_number_input)
        if not patient:
            err_msg = "Không tồn tại user trong cơ sở dữ liệu"
            return render_template("appointment_register.html", err_msg=err_msg)

        if current_user.user_role == UserRole.USER and current_user.id != patient['id']:
            err_msg = "Bạn không có SDT này hoặc bạn chưa thêm SDT này"
            return render_template("appointment_register.html", err_msg=err_msg)

        user_id = patient['id']

        appointment_id = dao.get_appointment_list_id_by_date(appointment_date)
        if not appointment_id:
            dao.create_appointment_list(appointment_date)
            appointment_id = dao.get_appointment_list_id_by_date(appointment_date)

        if dao.check_user_appointment_on_date(date=appointment_date, user_id=user_id):
            err_msg = "Bạn đã đăng ký rồi"
            return render_template("appointment_register.html", err_msg=err_msg)
        registered_patient_count = dao.count_patients_by_date(appointment_date)
        if registered_patient_count >= max_patient_limit:
            err_msg = "Số lượng bệnh nhân trong danh sách đã đầy, vui lòng đăng ký vào ngày khác"
            return render_template("appointment_register.html", err_msg=err_msg)
        dao.create_appointment_detail(appointment_id=appointment_id, user_id=user_id, appointment_time=appointment_time)
        suc_msg = "Đăng ký thành công"

        if not dao.get_medical_history(user_id=user_id):
            dao.add_medical_history(user_id=user_id)

    return render_template("appointment_register.html", err_msg=err_msg, suc_msg=suc_msg)



# ============================== NURSE ============================== #
# Thao tác của y tá
# Bao gồm các chức năng:
# - Xác nhận các bệnh nhân đăng ký hoăc xóa bệnh nhân khỏi danh sách khám
# - Xem các bệnh nhân nằm trong các AppoinmentList
# - Trường hợp xóa mà danh sách trống sẽ tự động xóa danh sách (optional)
# - Có thể xác nhận toàn bộ bệnh nhân trong ngày (optional)


@app.route('/confirm_patient', methods=['POST'])
def confirm_patient_process():
    err_msg = ''
    suc_msg = ''
    user_id = request.form.get('user_id_confirm')
    date = request.form.get('date_confirm')

    try:
        if not dao.check_user_appointment_on_date(user_id=user_id, date=date):
            err_msg = "Bệnh nhân không có trong danh sách khám ngày hôm nay."
        else:
            if dao.has_prescription(user_id=user_id, date=date):
                err_msg = "Bệnh nhân đã được xác nhận trước đó."
            else:
                dao.create_prescription(user_id=user_id)
                suc_msg = f"Xác nhận thành công cho bệnh nhân ID {user_id} vào ngày {date}."

                from send import send_email
                email = dao.get_email_by_user_id(user_id=user_id)
                subject = "Thông báo tạo phiếu khám"
                content = f"Xin chào,\n\nPhiếu khám cho user ID {user_id} đã được tạo thành công."
                send_email(email, subject, content)

    except Exception as e:
        err_msg = f"Đã xảy ra lỗi: {e}"

    return render_template("nurse.html", err_msg=err_msg, suc_msg=suc_msg, current_date=date)


@app.route('/delete_patient', methods=['POST'])
def delete_patient_process():
    err_msg = ''
    suc_msg = ''
    user_id = request.form.get('user_id_delete')
    date = request.form.get('date_delete')

    try:
        appointment_list_id = dao.get_appointment_list_id_by_date(date=date)
        if not appointment_list_id:
            err_msg = "Không tìm thấy danh sách khám trong ngày này."
            return render_template("nurse.html", err_msg=err_msg, suc_msg=suc_msg, current_date=date)

        if dao.has_prescription(user_id=user_id, date=date):
            err_msg = "Bệnh nhân đã có phiếu khám, không thể xóa."
        else:
            if dao.delete_appointment_detail_by_user_and_date(user_id=user_id, date=date):
                # if dao.delete_appointment_list_if_empty(appointment_list_id):
                #     suc_msg = "Danh sách khám đã bị xóa vì không còn bệnh nhân."
                # else:
                suc_msg = "Đã xóa chi tiết phiếu khám thành công."
            else:
                err_msg = "Không tìm thấy bệnh nhân trong danh sách khám."

    except Exception as e:
        err_msg = f"Đã xảy ra lỗi: {e}"

    return render_template("nurse.html", err_msg=err_msg, suc_msg=suc_msg, current_date=date)
@app.route("/load_appointment", methods=['GET', 'POST'])
def load_appointment_process():
    err_msg = ''
    user_list = []
    current_date = datetime.now().strftime('%Y-%m-%d')
    try:
        appointment_id = request.form.get('button_value')
        if appointment_id:
            appointment_details = dao.get_appointment_details(appointment_id)
            for i in appointment_details:
                user = dao.get_user(i.user_id)
                user_list.append(user)
            if not user_list:
                err_msg = "Không tìm thấy bệnh nhân nào thuộc danh sách"
            current_date_from_db = dao.get_date_by_appointment_list_id(appointment_id)
            if current_date_from_db:
                current_date = current_date_from_db.strftime('%Y-%m-%d')
        else:
            err_msg = "Appointment ID không hợp lệ hoặc không được gửi đến!"

    except Exception as ex:
        err_msg = f"Đã xảy ra lỗi: {str(ex)}"

    print(f"current_date: {current_date}")

    return render_template(
        "nurse.html",
        err_msg=err_msg,
        appointment_user_list=user_list,
        current_date=current_date
    )

@app.route("/save_chi_tiet_danh_sach_kham", methods=['get', 'post'])
def save_chi_tiet_danh_sach_kham():
    err_msg = ''
    suc_msg = ''
    current_date = request.form.get('current_date_submit')
    if request.method == 'POST':
        appointments_today = dao.get_appointment_today()
        if appointments_today:
            appointment_details = dao.get_appointment_details(appointment_detail_id=appointments_today[0][0])
            if appointment_details:
                for detail in appointment_details:
                    user_id = detail[2]
                    email = dao.get_email_by_user_id(user_id=user_id)
                    pk_today = dao.get_prescriptions_for_today(user_id=user_id)

                    if pk_today:
                        err_msg = "Danh sách khám đã được lưu"
                    else:
                        from send import send_email
                        dao.create_prescription(user_id)
                        err_msg = "Tạo thành công phiếu khám"
                        subject = "Thông báo tạo phiếu khám"
                        content = f"Xin chào,\n\nPhiếu khám cho user ID {user_id} đã được tạo thành công."
                        send_email(email, subject, content)
                        suc_msg = "Lưu phiếu khám thành công"
            else:
                err_msg = "Chưa có bệnh nhân nào đăng ký khám"

    return render_template("nurse.html", err_msg=err_msg, suc_msg=suc_msg, current_date=current_date)


# ============================== DOCTOR ============================== #
# Trang khám bệnh của Doctor
# Các chức năng chính:
# - Kiểm tra bệnh nhân có lịch khám hôm nay không và tải thông tin Prescription lên
# - Nếu không tồn tại sẽ không xuất hiện 2 nút thêm đơn thuốc và lưu đơn thuốc
# - Dữ liệu các loại thuốc được load sẵn
ma_phieu_kham_today = None
user_id_in_phieu_kham = None
@app.route("/doctor")
def doctor():
    info = dao.get_user(current_user.id)
    global ma_phieu_kham_today, user_id_in_phieu_kham
    ma_phieu_kham_today = None
    user_id_in_phieu_kham = None
    # session['ma_phieu_kham_today'] = None
    # session['user_id_in_phieu_kham'] = None
    return render_template("doctor.html", search_result = info)


# - ma_phieu_kham_today để lưu mã phiếu khám mình đang thao tác
# - user_id_in_phieu_kham để lưu user của phiếu khám đang thao tác
# - symptoms, diagnosis chỉ để giữ lại giá trị của các mục mình điền để không bị
#   mất đi khi thực hiện các thao tác
# - Trong route này sẽ thực hiện hai thao tác là tìm kiếm và thêm đơn thuốc
@app.route("/add_prescription", methods=['GET', 'POST'])
def add_prescription_process():
    err_msg = ''
    action = request.form.get('action')
    user_id = request.form.get('user_id')
    user_info = dao.get_user(user_id=user_id)

    global ma_phieu_kham_today, user_id_in_phieu_kham
    ma_phieu_kham_today = None
    user_id_in_phieu_kham = None
    # session['ma_phieu_kham_today'] = None
    # session['user_id_in_phieu_kham'] = None

    if not user_id:
        err_msg = "Không tồn tại bệnh nhân hoặc bệnh nhân chưa đăng ký khám"
        return render_template("doctor.html", err_msg=err_msg, user_id=user_id)
    medical_history = dao.load_disease_history(user_id=user_id)
    if action == "search_patient":
        user_prescriptions = dao.get_prescriptions_for_today(user_id=user_id)
        symptoms = ""
        diagnosis = ""
        if user_prescriptions:
            current_prescription = user_prescriptions[0]
            ma_phieu_kham_today = current_prescription['id']
            user_id_in_phieu_kham = current_prescription['user_id']
            # session['ma_phieu_kham_today'] = current_prescription['id']
            # session['user_id_in_phieu_kham'] = current_prescription['user_id']
            symptoms = user_prescriptions[0]['symptoms']
            diagnosis = user_prescriptions[0]['diagnosis']
        else:
            err_msg = "Không tồn tại bệnh nhân hoặc bệnh nhân chưa đăng ký khám"

        return render_template("doctor.html", err_msg=err_msg, search_result=user_info, user_id=user_id, symptoms=symptoms,
                               diagnosis=diagnosis, medical_history=medical_history)

    medicine_name = request.form.get('medicine')
    quantity = int(request.form.get('so_luong_thuoc', 0))

    user_prescriptions = dao.get_prescriptions_for_today(user_id=user_id)
    symptoms = user_prescriptions[0]['symptoms']
    diagnosis = user_prescriptions[0]['diagnosis']
    if not user_prescriptions:
        err_msg = "Phiếu khám chưa được tạo"
        return render_template("doctor.html", err_msg=err_msg, user_id=user_id, search_result=user_info)

    current_prescription = user_prescriptions[0]
    ma_phieu_kham_today = current_prescription['id']
    user_id_in_phieu_kham = current_prescription['user_id']
    # session['ma_phieu_kham_today'] = current_prescription['id']
    # session['user_id_in_phieu_kham'] = current_prescription['user_id']

    if not user_id_in_phieu_kham:
        err_msg = "Không tìm được mã bệnh nhân trong danh sách các phiếu khám"
        return render_template("doctor.html", err_msg=err_msg, user_id=user_id, search_result=user_info)

    thuoc = dao.get_medicines(medicine_name)

    if not thuoc:
        err_msg = "Không có thuốc này trong cơ sở dữ liệu"
        return render_template("doctor.html", err_msg=err_msg, user_id=user_id, search_result=user_info)

    thuoc_id = thuoc[0].id
    existing_medicine = dao.check_existing_medicine_in_prescription(medicine_id=thuoc_id,
                                                                    prescription_id=ma_phieu_kham_today)

    if existing_medicine:
        new_quantity = existing_medicine.quantity + quantity
        dao.update_medicine_quantity_in_prescription(
            medicine_id=thuoc_id, prescription_id=ma_phieu_kham_today, new_quantity=new_quantity
        )
    else:
        dao.save_chi_tiet_phieu_kham(
            so_luong_thuoc=quantity, thuoc_id=thuoc_id, phieu_kham_id=ma_phieu_kham_today
        )

    return render_template("doctor.html", err_msg=err_msg, user_id=user_id,
                           search_result=user_info,symptoms=symptoms, diagnosis=diagnosis, medical_history=medical_history)



@app.context_processor
def load_thuoc_trong_chi_tiet_pk():
    thuoc_trong_ctpk = dao.load_thuoc_in_chi_tiet_phieu_kham_today(
        user_id_in_phieu_kham)
    return {
        'medicines_in_prescription': thuoc_trong_ctpk
    }
    # thuoc_trong_ctpk = dao.load_thuoc_in_chi_tiet_phieu_kham_today(
    #     session['user_id_in_phieu_kham'])
    # return {
    #     'medicines_in_prescription': thuoc_trong_ctpk
    # }

@app.context_processor
def is_user_have_appointment_today():
    if user_id_in_phieu_kham == None:
        return {
            'is_user_have_appointment': False
        }
    is_user_have_appointment = dao.get_prescriptions_for_today(user_id_in_phieu_kham)
    if is_user_have_appointment:
        return {
            'is_user_have_appointment': True
        }
    return {
            'is_user_have_appointment': False
        }
    # if session['user_id_in_phieu_kham'] == None:
    #     return {
    #         'is_user_have_appointment': False
    #     }
    # is_user_have_appointment = dao.get_prescriptions_for_today(session['user_id_in_phieu_kham'])
    # if is_user_have_appointment:
    #     return {
    #         'is_user_have_appointment': True
    #     }
    # return {
    #         'is_user_have_appointment': False
    #     }


@app.route("/doctor_save_prescription", methods=['GET', 'POST'])
def doctor_save_prescription_process():
    err_msg = ''
    suc_msg = ''
    action = request.form.get('action')
    user_id = user_id_in_phieu_kham
    # user_id = session['user_id_in_phieu_kham']
    user_info = dao.get_user(user_id=user_id)
    user_prescriptions = dao.get_prescriptions_for_today(user_id=user_id)
    symptoms = request.form.get('trieu_chung')
    diagnosis = request.form.get('chuan_doan')
    if action.startswith('delete'):
        try:
            medicine_id = int(action.split('-')[1])
            prescription_id = ma_phieu_kham_today
            # prescription_id = session['ma_phieu_kham_today']
            dao.delete_medicine_from_prescription(medicine_id, prescription_id)
            suc_msg = f"Deleted medicine with ID {medicine_id} successfully."
        except Exception as e:
            err_msg = f"Failed to delete medicine: {str(e)}"
    elif action.startswith('save'):
        phieu_kham_id = ma_phieu_kham_today
        # phieu_kham_id = session['ma_phieu_kham_today']
        check_pk_id = dao.load_phieu_kham_id_today_by_phieu_kham_id(phieu_kham_id=phieu_kham_id)

        if check_pk_id:
            try:
                check_pk_id_numString = str(check_pk_id[0][0])
                if symptoms and diagnosis:
                    dao.update_phieu_kham(phieu_kham_id=check_pk_id_numString, trieu_chung=symptoms,
                                          chuan_doan=diagnosis)

                    benh_id = dao.load_benh_id_by_ten_benh(diagnosis)
                    lsb_id = dao.load_lich_su_benh_id_by_phieu_kham_id(check_pk_id_numString)

                    if lsb_id and benh_id:
                        dao.add_medical_history_detail(medical_history_id=lsb_id[0][0], disease_id=benh_id[0][0])
                        suc_msg = f"Lưu thành công phiếu khám có mã phiếu là {check_pk_id_numString}"
                    else:
                        err_msg = "Lịch sử bệnh hoặc bệnh không tồn tại trong cơ sở dữ liệu"
                else:
                    err_msg = "Chưa nhập chuẩn đoán và triệu chứng"
            except Exception as e:
                err_msg = f"An error occurred while saving the prescription: {str(e)}"
        else:
            err_msg = "Không tồn tại phiếu khám này"
    return render_template("doctor.html", err_msg=err_msg, suc_msg=suc_msg,
                           user_id=user_id, search_result=user_info, symptoms=symptoms, diagnosis=diagnosis)


# ============================== PAYMENT ============================== #
@app.route("/process_payment", methods=['POST'])
def process_payment():
    user_id = request.form.get('user_id')
    err_msg = ''
    suc_msg = ''
    user_bill = None
    try:
        with open("app/data/rules.json", "r") as file:
            rules = json.load(file)
        tien_kham = rules["tien_kham"]
        today_prescriptions = dao.get_prescriptions_for_today(user_id=user_id)
        if today_prescriptions:
            bill = dao.bill_for_one_user_by_id(user_id=user_id)
            if bill:
                bill_id = dao.save_bill_for_user(
                    date=bill['date'],
                    total_amount=bill['total_price'] + tien_kham,
                    user_id=user_id
                )
                suc_msg = "Thanh toán thành công!"
                dao.payment(bill_id=bill_id)
            else:
                err_msg = "Không tìm thấy thông tin hóa đơn."
        else:
            err_msg = "Không có phiếu khám cho bệnh nhân này."
    except Exception as e:
        err_msg = f"Lỗi khi xử lý thanh toán: {str(e)}"

    return render_template("cashier.html", err_msg=err_msg, suc_msg=suc_msg, user_bill=user_bill)



@app.route("/cashier", methods=['get', 'post'])
def cashier():
    err_msg = ''
    user_id = request.args.get('kw')
    user_bill = None
    if user_id:
        with open("app/data/rules.json", "r") as file:
            rules = json.load(file)

        tien_kham = rules["tien_kham"]
        today_prescriptions = dao.get_prescriptions_for_today(user_id=user_id)
        if today_prescriptions:
            phieu_kham_id = today_prescriptions[0]['id']
            # phieu_kham = dao.get_prescription_details(today_prescriptions[0]['id'])
            hoa_don = dao.load_hoa_don_by_phieu_kham_id(phieu_kham_id=phieu_kham_id)
            if hoa_don:
                err_msg = "Hóa đơn đã được thanh toán!"
                return render_template("cashier.html", err_msg=err_msg, tien_kham=tien_kham, user_bill=user_bill)
            else:
                user_bill = dao.bill_for_one_user_by_id(user_id=user_id)
        else:
            err_msg = "Không tồn tại hóa đơn của bệnh nhân này trong ngày hôm nay."
        return render_template("cashier.html", err_msg=err_msg, tien_kham=tien_kham, user_bill=user_bill)
    return render_template("cashier.html", err_msg=err_msg, user_bill=user_bill)

# ============================== MEDICAL HISTORY ============================== #
@app.route("/medical_history")
def medical_history_process():
    medical_history_records = []
    if current_user.is_authenticated:
        if current_user.user_role == UserRole.USER:
            medical_history_records = dao.get_user_prescriptions(current_user.id)
        else:
            medical_history_records = dao.get_user_prescriptions()
    kw = request.args.get('kw')
    err_msg = ''
    all_prescriptions = []

    if kw:
        all_prescriptions = dao.load_prescription_data(user_id=kw)
        if all_prescriptions:
            medical_history_records = dao.get_user_prescriptions(user_id=kw)
        else:
            medical_history_records = []
    else:
        all_users = dao.load_users()
        for user in all_users:
            user_prescription_data = dao.load_prescription_data(user_id=user.id)
            if user_prescription_data:
                data = {'user': user, 'prescription': user_prescription_data}
                for i in data['prescription']:
                    all_prescriptions.append(i)
    for i in medical_history_records:
        print(i)
    for i in all_prescriptions:
        print(i)
    if kw and not medical_history_records:
        err_msg = 'Không tìm thấy bệnh nhân'
    return render_template("medical_history.html", err_msg=err_msg, patient_prescription=medical_history_records,
                           all_prescriptions=all_prescriptions)
# ============================== INVOICE HISTORY ============================== #

@app.route("/invoices", methods=['GET'])
@login_required
def view_invoices():
    err_msg = ''
    user_id = request.args.get('user_id')
    invoices = []

    try:
        if user_id:
            invoices = dao.get_invoices(user_id=user_id)
            if not invoices:
                err_msg = "Không tìm thấy hóa đơn nào cho bệnh nhân này."
        else:
            invoices = dao.get_invoices()
    except Exception as e:
        err_msg = f"Lỗi xảy ra: {e}"
    print(invoices)
    return render_template("invoice_history.html", invoices=invoices, err_msg=err_msg)

# ============================== CONTEXT PROCESSOR ============================== #
@app.context_processor
def load_appointment_user_list():
    appointment_user_list = []
    dsk = dao.get_appointment_today()
    if dsk:
        user_id_in_dsk = dao.get_appointment_details(dsk[0][0])
        n = len(user_id_in_dsk)
        for i in range(0, n):
            appointment_user_list.append(dao.get_user(user_id_in_dsk[i][2]))
    return {
        'appointment_user_list': appointment_user_list
    }

@app.context_processor
def load_appointment_date():
    today = datetime.now()
    dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    return {
        'appointment_dates': dates
    }

@app.context_processor
def load_appointment_time():
    times = [
        "08:00", "09:00", "10:00", "11:00",
        "13:00", "14:00", "15:00", "16:00"
    ]
    return {
        'appointment_times': times
    }

@app.context_processor
def get_danh_sach_kham():
    danh_sach_kham = dao.load_danh_sach_kham()
    return {
        'danh_sach_kham': danh_sach_kham
    }

@app.context_processor
def load_today_date():
    today = datetime.now()
    return {
        'today_date': today.strftime('%Y-%m-%d')
    }

@app.context_processor
def load_user_role():
    return {'UserRole': UserRole}

@app.context_processor
def load_diseases():
    diseases = dao.load_diseases()
    return {
        'diseases': diseases
    }

@app.context_processor
def load_medicines():
    medicines = dao.get_medicines()
    return {
        'medicines': medicines
    }


@app.context_processor
def load_phieu_kham():
    phieu_kham = dao.get_prescriptions_for_today()
    return {
        'phieu_kham': phieu_kham
    }