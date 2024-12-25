from sqlalchemy.orm import joinedload

from app.models import *
from app import app, db
import hashlib
import cloudinary.uploader
from flask_login import current_user
from sqlalchemy import func
from sqlalchemy.sql.functions import user

# ========================== TEST ZONE ========================== #

def get_invoice_details_by_user_id(user_id):
    query = db.session.query(Invoice.id, Invoice.date, Invoice.total_amount) \
        .filter(Invoice.user_id == user_id)
    return query.all()

def get_invoice_ids_by_user_id(user_id):
    try:
        # Query the Invoice table to find all invoices for the user
        invoices = Invoice.query.filter_by(user_id=user_id).all()
        return [invoice.id for invoice in invoices]
    except Exception as e:
        print(f"Error retrieving invoice IDs for user {user_id}: {str(e)}")
        return []



def delete_medicine_from_prescription(medicine_id, prescription_id):
    try:
        db.session.query(PrescriptionDetail).filter(
            PrescriptionDetail.medicine_id == medicine_id,
            PrescriptionDetail.prescription_id == prescription_id
        ).delete()
        db.session.commit()
    except Exception as e:
        print(f"Error deleting medicine from prescription: {e}")
        db.session.rollback()
def check_existing_medicine_in_prescription(medicine_id, prescription_id):
    return db.session.query(PrescriptionDetail).filter(
        PrescriptionDetail.medicine_id == medicine_id,
        PrescriptionDetail.prescription_id == prescription_id
    ).first()

def update_medicine_quantity_in_prescription(medicine_id, prescription_id, new_quantity):
    try:
        prescription_detail = db.session.query(PrescriptionDetail).filter(
            PrescriptionDetail.medicine_id == medicine_id,
            PrescriptionDetail.prescription_id == prescription_id
        ).first()
        if prescription_detail:
            prescription_detail.quantity = new_quantity
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating medicine quantity: {e}")

# ================================================================ #
def load_prescription_details_today(ma_phieu_kham_today):
    query = db.session.query(PrescriptionDetail.medicine_id, Medicine.name, Medicine.unit,
                             PrescriptionDetail.quantity) \
        .join(Medicine, Medicine.id.__eq__(PrescriptionDetail.medicine_id), isouter=True) \
        .filter(PrescriptionDetail.prescription_id.__eq__(ma_phieu_kham_today))
    return query.all()


def delete_medicine_by_id(medicine_id):
    try:
        db.session.query(Medicine).filter(Medicine.id == medicine_id).delete()
        db.session.commit()
    except Exception as e:
        print(f"Error while deleting medicine: {e}")
        db.session.rollback()


def get_today_string():
    return datetime.now().strftime('%Y-%m-%d')


def commit_session():
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Database Commit Error: {str(e)}")

def update_thuoc_description(thuoc_id, description):
    try:
        medicine = Medicine.query.get(thuoc_id)
        if medicine:
            medicine.description = description
            db.session.commit()
    except Exception as e:
        print(f"Error in update_thuoc_description: {e}")
        db.session.rollback()


def delete_thuoc(thuoc_id):
    try:
        medicine = Medicine.query.get(thuoc_id)
        if medicine:
            db.session.delete(medicine)
            db.session.commit()
    except Exception as e:
        print(f"Error in delete_thuoc: {e}")
        db.session.rollback()


def load_prescription_data(user_id=None):
    try:
        query = (
            db.session.query(
                PrescriptionDetail.prescription_id,
                Prescription.date.label("prescription_date"),
                Medicine.name.label("medicine_name"),
                PrescriptionDetail.quantity.label("medicine_quantity"),
                Medicine.unit.label("medicine_unit"),
                Medicine.description.label("medicine_description"),
                Prescription.user_id
            )
            .join(Prescription, Prescription.id == PrescriptionDetail.prescription_id)
            .join(Medicine, Medicine.id == PrescriptionDetail.medicine_id)
            .order_by(PrescriptionDetail.prescription_id)
        )
        if (user_id):
            query = query.filter(Prescription.user_id == user_id)
        results = query.all()
        formatted_results = [
            {
                "prescription_id": row.prescription_id,
                "date": row.prescription_date,
                "medicine_name": row.medicine_name,
                "quantity": row.medicine_quantity,
                "unit": row.medicine_unit,
                "description": row.medicine_description,
                "user_id": row.user_id,
            }
            for row in results
        ]
        return formatted_results
    except Exception as ex:
        print(f"Error fetching prescription data: {ex}")
        return None


def add_user(full_name, username, password, birth_date, gender, phone_number, address, avatar=None,
             user_role=UserRole.USER, status=True):
    if User.query.filter((User.username == username) | (User.phone_number == phone_number)).first():
        raise Exception('Username or phone number is already in use.')

    avatar_path = avatar or "static/default-avatar.png"
    new_user = User(
        full_name=full_name, username=username, password=password, birth_date=birth_date,
        gender=gender, phone_number=phone_number, address=address, avatar=avatar_path,
        user_role=user_role, status=status,
    )
    db.session.add(new_user)
    commit_session()


def get_user_by_username(username):
    return User.query.filter_by(username=username).first()


def get_user_by_phone(phone_number):
    return User.query.filter_by(phone_number=phone_number).first()


def load_diseases():
    return Disease.query.all()


def load_categories():
    return MedicineCategory.query.all()


def load_users():
    return User.query.all()


def get_users_by_phone(phone_number=None):
    query = db.session.query(User.id, User.full_name, User.phone_number)
    if phone_number:
        query = query.filter(User.phone_number.__eq__(phone_number))
    return query.all()


def auth_user(username, password, role=None):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    query =   User.query.filter(User.username.__eq__(username.strip()), User.password.__eq__(password))
    if role != None:
        query = query.filter(User.user_role.__eq__(role))
    return query.first()


def get_user_by_id(user_id):
    try:
        return User.query.filter(User.id == user_id).first()
    except Exception as e:
        print(f"Error fetching user by ID {user_id}: {e}")
        return None


def count_medicine_by_cate():
    return db.session.query(MedicineCategory.id, MedicineCategory.category_name, func.count(Medicine.id)) \
        .join(Medicine, Medicine.category_id.__eq__(MedicineCategory.id), isouter=True) \
        .group_by(MedicineCategory.id).order_by(-MedicineCategory.category_name).all()


def count_user():
    return db.session.query(User.user_role, func.count(User.id)).group_by(User.user_role).all()


def stats_by_medic(kw=None, from_date=None, to_date=None):
    query = db.session.query(Medicine.id, Medicine.name, Medicine.unit,
                             func.sum(PrescriptionDetail.quantity)) \
        .join(Medicine, Medicine.id.__eq__(PrescriptionDetail.medicine_id), isouter=True)

    if kw:
        query = query.filter(Medicine.name.contains(kw))

    if from_date:
        query = query.filter(Prescription.date.__ge__(from_date))

    if to_date:
        query = query.filter(Prescription.date.__le__(to_date))

    return query.group_by(Medicine.id).order_by(-Medicine.id).all()



def stats_by_revenue(month=None):
    # Invoice, User
    query = db.session.query(Invoice.date, func.count(User.id), func.sum(Invoice.total_amount)).join(Invoice,
                                                                                                     Invoice.user_id.__eq__(
                                                                                                         User.id))
    if month:
        query = query.filter(Invoice.date.contains(month))

    return query.group_by(Invoice.date).all()


# ====================================================================================
def bill_for_one_user_by_id(user_id):
    query = db.session.query(
        User.id.label("user_id"),
        User.full_name.label("user_name"),
        Prescription.id.label("prescription_id"),
        Prescription.user_id.label("prescription_user_id"),
        func.sum(PrescriptionDetail.quantity * Medicine.price).label("total_price"),
        Prescription.date.label("date")
    ).join(
        Prescription, Prescription.id.__eq__(PrescriptionDetail.prescription_id)
    ).join(
        Medicine, Medicine.id.__eq__(PrescriptionDetail.medicine_id)
    ).join(
        User, User.id.__eq__(Prescription.user_id)
    )

    query = query.filter(User.id.__eq__(user_id))
    today = datetime.now()
    today_string = today.strftime("%Y-%m-%d")
    query = query.filter(Prescription.date.__eq__(today_string))

    result = query.group_by(User.id, Prescription.id, Prescription.date).first()

    if result:
        return {
            "user_id": result.user_id,
            "user_name": result.user_name,
            "prescription_id": result.prescription_id,
            "prescription_user_id": result.prescription_user_id,
            "total_price": float(result.total_price) if result.total_price else 0.0,
            "date": result.date
        }
    else:
        return None


def save_bill_for_user(date, total_amount, user_id):
    b = Invoice(date=date, total_amount=total_amount, user_id=user_id)
    db.session.add(b)
    db.session.commit()


def check_payment_status(bill_id):
    bill = Invoice.query.get(bill_id)
    if bill:
        return bill.payment_completed


def payment(bill_id):
    bill = Invoice.query.get(bill_id)
    if bill:
        bill.payment_completed = True
        db.session.commit()


def load_hoa_don_by_phieu_kham_id(phieu_kham_id=None):  # Viết cái câu truy vấn ngon lành mà không xài được tức ghê -_-
    query = db.session.query(User.full_name, Invoice.date, Invoice.total_amount) \
        .join(Invoice, Invoice.user_id.__eq__(User.id)) \
        .join(Prescription, Prescription.user_id.__eq__(User.id))

    today = datetime.now()
    todayString = str(today)[0:10]
    query = query.filter(Invoice.date.__eq__(todayString))

    if phieu_kham_id:
        query = query.filter(Prescription.id.__eq__(phieu_kham_id))

    return query.group_by(User.full_name, Invoice.date, Invoice.total_amount).all()


def load_hoa_don():
    query = db.session.query(Invoice.id, Prescription.id, User.full_name, Invoice.date, Invoice.total_amount) \
        .join(Invoice, Invoice.user_id.__eq__(User.id)) \
        .join(Prescription, Prescription.user_id.__eq__(User.id))

    today = datetime.now()
    todayString = str(today)[0:10]
    query = query.filter(Invoice.date.__eq__(todayString))
    query = query.filter(Prescription.date.__eq__(todayString))

    return query.group_by(Invoice.id, Prescription.id, User.full_name, Invoice.date, Invoice.total_amount).order_by(
        Invoice.id).all()


# ====================================================================================


def get_prescription_details(prescription_id):
    result = db.session.query(
        Prescription.id.label("prescription_id"),
        Prescription.name.label("name"),
        Prescription.date.label("date"),
        Prescription.symptoms.label("symptoms"),
        Prescription.diagnosis.label("diagnosis"),
        Prescription.user_id.label("user_id")
    ).filter(
        Prescription.id == prescription_id
    ).first()

    if result:
        return {
            "prescription_id": result.prescription_id,
            "name": result.name,
            "date": result.date.strftime("%Y-%m-%d") if result.date else None,
            "symptoms": result.symptoms,
            "diagnosis": result.diagnosis,
            "user_id": result.user_id
        }
    return None


def load_danh_sach_kham():
    return db.session.query(AppointmentList.id, AppointmentList.name, AppointmentList.date).all()


def create_appointment_list():
    dsk = AppointmentList()
    db.session.add(dsk)
    db.session.commit()


def get_appointments_for_today():
    query = db.session.query(AppointmentList.id, AppointmentList.name, AppointmentList.date)
    today = datetime.now()
    todayString = str(today)[0:10]
    query = query.filter(AppointmentList.date.__eq__(todayString))
    return query.all()


def create_appointment_detail(adppointment_id, user_id):
    ctdsk = AppointmentDetail(appointment_list_id=adppointment_id, user_id=user_id)
    db.session.add(ctdsk)
    db.session.commit()


def load_chi_tiet_danh_sach_kham_today(user_id=None):
    query = db.session.query(AppointmentDetail.id, AppointmentDetail.appointment_list_id, AppointmentDetail.user_id) \
        .join(AppointmentList, AppointmentList.id.__eq__(AppointmentDetail.appointment_list_id))
    test = db.session.query(AppointmentList.id, AppointmentList.name, AppointmentList.date)
    today = datetime.now()
    todayString = str(today)[0:10]
    query = query.filter(AppointmentList.date.__eq__(todayString))

    if user_id:
        query = query.filter(AppointmentDetail.user_id.__eq__(user_id))

    return query.all()


# ====================================================================================
def get_user_in_danh_sach_kham():
    query = db.session.query(AppointmentDetail.id, AppointmentDetail.appointment_list_id, User.id, User.full_name,
                             User.gender, User.birth_date, User.address, User.phone_number) \
        .join(User, User.id.__eq__(AppointmentDetail.user_id))

    return query.all()


def get_appointment(appointment_id=None):
    query = db.session.query(AppointmentList.id, AppointmentList.name, AppointmentList.date)
    if appointment_id:
        query = query.filter(AppointmentList.id.__eq__(appointment_id))
    return query.all()

def get_appointment_today():
    query = db.session.query(
        AppointmentList.id,
        AppointmentList.name,
        AppointmentList.date
    )
    today = datetime.now()
    todayString = str(today)[0:10]
    query = query.filter(AppointmentList.date.__eq__(todayString))
    return query.all()


def get_appointment_details(appointment_detail_id=None):

    query = db.session.query(
        AppointmentDetail.id.label('appointment_detail_id'),
        AppointmentDetail.appointment_list_id.label('appointment_list_id'),
        AppointmentDetail.user_id.label('user_id')
    )
    if appointment_detail_id:
        query = query.filter(AppointmentDetail.appointment_list_id.__eq__(appointment_detail_id))
    return query.all()


# def load_users_by_user_id(user_id=None):
#     query = db.session.query(User.id, User.full_name,
#                              User.gender, User.birth_date, User.address, User.phone_number)

#     if user_id:
#         query = query.filter(User.id.__eq__(user_id))
#     return query.all()
def load_users_by_user_id(user_id=None):
    query = db.session.query(
        User.id, 
        User.full_name,
        User.gender, 
        User.birth_date, 
        User.address, 
        User.phone_number
    )
    if user_id:
        query = query.filter(User.id == user_id)
    
    results = query.all()
    formatted_results = [
        {
            "user_id": row.id,
            "full_name": row.full_name,
            "gender": row.gender,
            "birth_date": row.birth_date,
            "address": row.address,
            "phone_number": row.phone_number
        }
        for row in results
    ]
    return formatted_results



# ====================================================================================

def get_newest_appoinment_id():
    return db.session.query(func.max(AppointmentList.id)).first()[0]


def create_prescription(user_id):
    if not user_id:
        raise ValueError("User ID không hợp lệ")
    prescription = Prescription(user_id=user_id, date=datetime.now())
    db.session.add(prescription)
    db.session.commit()
    return prescription



# def get_prescriptions_for_today(user_id=None):
#     query = db.session.query(Prescription.id, Prescription.name, Prescription.date, Prescription.symptoms,
#                              Prescription.diagnosis, Prescription.user_id, User.full_name).join(User, User.id.__eq__(
#         Prescription.user_id))
#     today = datetime.now()
#     todayString = str(today)[0:10]
#     query = query.filter(Prescription.date.__eq__(todayString))
#
#     if user_id:
#         query = query.filter(Prescription.user_id.__eq__(user_id))
#
#     return query.all() or []

def get_prescriptions_for_today(user_id=None):
    try:
        query = db.session.query(
            Prescription.id.label('id'),
            Prescription.name.label('name'),
            Prescription.date.label('date'),
            Prescription.symptoms.label('symptoms'),
            Prescription.diagnosis.label('diagnosis'),
            Prescription.user_id.label('user_id'),
            User.full_name.label('full_name')
        ).join(User, User.id == Prescription.user_id)

        today = datetime.now()
        today_string = today.strftime("%Y-%m-%d")

        query = query.filter(Prescription.date == today_string)
        if user_id:
            query = query.filter(Prescription.user_id == user_id)
        results = query.all() or []
        formatted_results = [
            {
                "id": row.id,
                "name": row.name,
                "date": row.date,
                "symptoms": row.symptoms,
                "diagnosis": row.diagnosis,
                "user_id": row.user_id,
                "full_name": row.full_name,
            }
            for row in results
        ]

        return formatted_results
    except Exception as e:
        print(f"Error fetching prescriptions for today: {e}")
        return []
# ====================================================================================
def get_medicines(ten_thuoc=None):
    query = db.session.query(Medicine.id,
                             Medicine.name,
                             Medicine.price,
                             Medicine.unit,
                             Medicine.description,
                             Medicine.category_id)
    if ten_thuoc:
        query = query.filter(Medicine.name.__eq__(ten_thuoc))

    return query.all()


def save_chi_tiet_phieu_kham(so_luong_thuoc=None, thuoc_id=None, phieu_kham_id=None):
    ctpk = PrescriptionDetail(quantity=so_luong_thuoc, medicine_id=thuoc_id, prescription_id=phieu_kham_id)
    db.session.add(ctpk)
    db.session.commit()


def update_phieu_kham(phieu_kham_id=None, trieu_chung=None, chuan_doan=None):
    phieu_kham = Prescription.query.filter_by(id=phieu_kham_id).first()
    phieu_kham.symptoms = trieu_chung
    phieu_kham.diagnosis = chuan_doan

    db.session.commit()


def load_phieu_kham_id_today_by_phieu_kham_id(phieu_kham_id=None):
    query = db.session.query(Prescription.id)
    today = datetime.now()
    todayString = str(today)[0:10]
    if phieu_kham_id:
        query = query.filter(Prescription.id.__eq__(phieu_kham_id))
    query = query.filter(Prescription.date.__eq__(todayString))

    return query.all()


def load_thuoc_in_chi_tiet_phieu_kham_today(user_id=None):
    if user_id == 0:
        return []
    query = db.session.query(Medicine.id, Medicine.name, Medicine.unit, PrescriptionDetail.quantity,
                             Medicine.description,
                             PrescriptionDetail.prescription_id,
                             Prescription.user_id
                             ) \
        .join(Medicine, Medicine.id.__eq__(PrescriptionDetail.medicine_id)) \
        .join(Prescription, Prescription.id.__eq__(PrescriptionDetail.prescription_id))

    today = datetime.now()
    todayString = str(today)[0:10]
    query = query.filter(Prescription.date.__eq__(todayString))

    if user_id:
        query = query.filter(Prescription.user_id.__eq__(user_id))

    return query.all() or []


# ====================================================================================

def add_medical_history(user_id):
    lsb = MedicalHistory(user_id=user_id)
    db.session.add(lsb)
    db.session.commit()


def load_lich_su_benh(user_id=None):
    query = db.session.query(MedicalHistory.id, MedicalHistory.name, MedicalHistory.user_id)

    if user_id:
        query = query.filter(MedicalHistory.user_id.__eq__(user_id))

    return query.all()


def save_chi_tiet_lich_su_benh(lich_su_benh_id=None, benh_id=None):
    lsb = MedicalHistoryDetail(medical_history_id=lich_su_benh_id, disease_id=benh_id)
    db.session.add(lsb)
    db.session.commit()


def load_benh_id_by_ten_benh(ten_benh=None):
    query = db.session.query(Disease.id)

    if ten_benh:
        query = query.filter(Disease.name.__eq__(ten_benh))

    return query.all()


def load_lich_su_benh_id_by_phieu_kham_id(phieu_kham_id=None):
    query = db.session.query(MedicalHistory.id) \
        .join(User, User.id.__eq__(MedicalHistory.user_id)) \
        .join(Prescription, Prescription.user_id.__eq__(User.id))

    if phieu_kham_id:
        query = query.filter(Prescription.id.__eq__(phieu_kham_id))

    return query.group_by(MedicalHistory.id).all()


# ====================================================================================
def get_user_prescriptions(user_id=None):
    try:
        query = db.session.query(
            User.id.label('user_id'),
            User.full_name.label('full_name'),
            Prescription.date.label('prescription_date'),
            Prescription.symptoms.label('symptoms'),
            Prescription.diagnosis.label('diagnosis'),
            Prescription.id.label('prescription_id')
        ) \
            .join(Prescription, Prescription.user_id == User.id)

        if user_id:
            query = query.filter(User.id == user_id)

        query = query.distinct(Prescription.id).order_by(Prescription.date.desc(), Prescription.id)
        results = query.all()
        formatted_results = [
            {
                "prescription_id": row.prescription_id,
                "date": row.prescription_date,
                "symptoms": row.symptoms,
                "diagnosis": row.diagnosis,
                "user_id": row.user_id,
                "full_name": row.full_name,
            }
            for row in results
        ]

        return formatted_results or []

    except Exception as ex:
        print(f"Error fetching prescription data: {ex}")
        return None


# ====================================================================================
def get_appointment_counts_for_today():
    query = db.session.query(AppointmentList.id, func.count(AppointmentDetail.id)) \
        .join(AppointmentDetail, AppointmentDetail.appointment_list_id.__eq__(AppointmentList.id))
    today = datetime.now()
    todayString = str(today)[0:10]
    query = query.filter(AppointmentList.date.__eq__(todayString))

    return query.group_by(AppointmentList.id).all()
# ====================================================================================


