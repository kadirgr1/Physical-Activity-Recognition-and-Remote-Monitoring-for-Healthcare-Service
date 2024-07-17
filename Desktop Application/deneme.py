import os
import cv2
import mediapipe as mp
import numpy as np
import tkinter as tk
import datetime
import matplotlib.pyplot as plt
from tkinter import ttk
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo, showerror
from PIL import Image, ImageTk
from tkinter import Label,  Tk
from collections import defaultdict
import pyrebase

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Şu anki tarihi ve saati al
current_time = datetime.datetime.now()

# Tarihi belirli bir formatta biçimlendir
formatted_time = current_time.strftime("%Y-%m-%d %H:%M")
Movements = "Movements"



# Firebase konfigürasyonu
firebase_config = {
    "apiKey": "AIzaSyAK6Dvuxwoy9EwaLm6pmNiRuSnUUptz4Gg",
    "authDomain": "testproject-ae7e8.firebaseapp.com",
    "projectId": "testproject-ae7e8",
    "storageBucket": "testproject-ae7e8.appspot.com",
    "messagingSenderId": "722858356466",
    "appId": "1:722858356466:web:71b5e3cc9666e9dd0d2a6b",
    "measurementId": "G-SB1ZKL9LKX",
    "databaseURL": ""
}
firebase = pyrebase.initialize_app(firebase_config)
storage = firebase.storage()
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()


def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle
    return angle


def login():
    def validate_login():
        email = mail_giris.get()
        # Query Firestore to find the document with the provided email
        user_ref = db.collection('Patients').where('mail', '==', email).limit(1)
        docs = user_ref.stream()

        login_successful = False
        for doc in docs:
            user_data = doc.to_dict()
            # Check if the retrieved document's password matches the provided password
            if user_data['password'] == password_giris.get():
                login_successful = True
                break

        if login_successful:
            select_file(email)
            # Add any further actions you want to take upon successful login
        else:
            showerror(
                title='Invalid Credentials',
                message='Invalid mail or password.'
            )

    login_window = tk.Toplevel(root)
    login_window.title("LogIn")
    login_window.geometry('479x359')

    global bg_image
    bg_image = tk.PhotoImage(file="resim.png")
    background_label = tk.Label(login_window, image=bg_image)
    background_label.place(relwidth=1, relheight=1)

    mail_label = ttk.Label(login_window, text='Mail:')
    mail_label.pack()
    mail_giris = ttk.Entry(login_window)
    mail_giris.pack()

    password_label = ttk.Label(login_window, text='Password:')
    password_label.pack()
    password_giris = ttk.Entry(login_window, show="*")
    password_giris.pack()

    # Add an "Ok" button to confirm login details
    ok_button = ttk.Button(login_window, text="Ok", command=validate_login)
    ok_button.pack()


def register():
    signup_window = tk.Toplevel(root)
    signup_window.title("Sign Up")
    signup_window.geometry('479x359')

    global bg_image
    bg_image = tk.PhotoImage(file="resim.png")
    background_label = tk.Label(signup_window, image=bg_image)
    background_label.place(relwidth=1, relheight=1)

    # 'ad_giris' adında bir Entry nesnesi oluşturma
    ad_label = ttk.Label(signup_window, text='Name:')
    ad_label.pack()
    ad_giris = ttk.Entry(signup_window)
    ad_giris.pack()

    soyad_label = ttk.Label(signup_window, text='Surname:')
    soyad_label.pack()
    soyad_giris = ttk.Entry(signup_window)
    soyad_giris.pack()

    mail_label = ttk.Label(signup_window, text='Mail:')
    mail_label.pack()
    mail_giris = ttk.Entry(signup_window)
    mail_giris.pack()

    password_label = ttk.Label(signup_window, text='Password:')
    password_label.pack()
    password_giris = ttk.Entry(signup_window, show="*")
    password_giris.pack()

    phone_label = ttk.Label(signup_window, text='Phone Number:')
    phone_label.pack()
    phone_giris = ttk.Entry(signup_window)
    phone_giris.pack()

    doctor_ID_label = ttk.Label(signup_window, text='Doctor ID :')
    doctor_ID_label.pack()
    doctor_ID_giris = ttk.Entry(signup_window)  # doctor_ID_giris burada tanımlanmalı
    doctor_ID_giris.pack()

    def register_user():
        ad = ad_giris.get()
        soyad = soyad_giris.get()
        mail = mail_giris.get()
        password = password_giris.get()
        phone = phone_giris.get()
        doctor_ID = doctor_ID_giris.get()

        try:
            phone = int(phone)
        except ValueError:
            showerror(
                title='Invalid Input',
                message='Phone number must be an integer.'
            )
            return
        if not (ad and soyad and mail and password and doctor_ID):
            showerror(
                title='Missing Information',
                message='Please fill in all fields'
            )
            return

        if not validate_doctor_id(doctor_ID):
            showerror(
                title='Invalid Doctor ID',
                message='The Doctor ID entered does not exist. Please check and try again.'
            )
            return

        patients_ref = db.collection('Patients')
        patients_docs = patients_ref.get()
        for doc in patients_docs:
            if mail == doc.to_dict()['mail']:
                showerror(
                    title='Hata',
                    message='This email address is already in use..'
                )
                return

        db.collection('Patients').add(
            {'name': ad, 'surname': soyad, 'mail': mail, 'password': password, 'phone': phone, 'doctor_ID': doctor_ID})
        signup_window.destroy()  # Close sign-up window
        root.deiconify()  # Bring back the main window

        select_file(mail)

    register_button = ttk.Button(signup_window, text="Okey", command=register_user)
    register_button.pack()


def validate_doctor_id(doctor_id):
    """Validate the given doctor_id against the 'Doctors' collection in Firestore."""
    doctors_ref = db.collection('Doctors')
    doc = doctors_ref.document(doctor_id).get()
    return doc.exists
def show_movement_info(x_value, root):
    image_path = ""
    if x_value == "1. Movement":
        # Bilgi iletişim kutusunu göster
        showinfo('Camera angle', 'When choosing the video, make sure that it is like a camera angle in the image')
        image_path = 'C:/Users/kadir/PycharmProjects/denemeproject/Görseller/movement1_1.png'
        image = Image.open(image_path)

        # Görseli ekranda göster
        plt.imshow(image)
        plt.axis('off')  # Eksenleri kapat
        #plt.show()

    elif x_value == "2. Movement":
        showinfo('Camera angle', 'When choosing the video, make sure that it is like a camera angle in the image')
        image_path = 'C:/Users/kadir/PycharmProjects/denemeproject/Görseller/movement2_1.png'

        image = Image.open(image_path)
        # Görseli ekranda göster
        plt.imshow(image)
        plt.axis('off')  # Eksenleri kapat
        #plt.show()

    elif x_value == "3. Movement":
        showinfo('Camera angle', 'When choosing the video, make sure that it is like a camera angle in the image')
        image_path = 'C:/Users/kadir/PycharmProjects/denemeproject/Görseller/movement3_1.png'

        image = Image.open(image_path)
        # Görseli ekranda göster
        plt.imshow(image)
        plt.axis('off')  # Eksenleri kapat
        #plt.show()

    elif x_value == "4. Movement":
        showinfo('Camera angle', 'When choosing the video, make sure that it is like a camera angle in the image')
        image_path = 'C:/Users/kadir/PycharmProjects/denemeproject/Görseller/movement4_1.png'

        image = Image.open(image_path)
        # Görseli ekranda göster
        plt.imshow(image)
        plt.axis('off')  # Eksenleri kapat
        #plt.show()

    elif x_value == "5. Movement":
        showinfo('Camera angle', 'When choosing the video, make sure that it is like a camera angle in the image')
        image_path = 'C:/Users/kadir/PycharmProjects/denemeproject/Görseller/movement5_1.png'

        image = Image.open(image_path)
        # Görseli ekranda göster
        plt.imshow(image)
        plt.axis('off')  # Eksenleri kapat
        #plt.show()

    elif x_value == "6.. Movement":
        showinfo('Camera angle', 'When choosing the video, make sure that it is like a camera angle in the image')
        image_path = 'C:/Users/kadir/PycharmProjects/denemeproject/Görseller/movement6_1.png'

        image = Image.open(image_path)
        # Görseli ekranda göster
        plt.imshow(image)
        plt.axis('off')  # Eksenleri kapat
        #plt.show()

    elif x_value == "7. Movement":
        showinfo('Camera angle', 'When choosing the video, make sure that it is like a camera angle in the image')
        image_path = 'C:/Users/kadir/PycharmProjects/denemeproject/Görseller/movement7_1.png'

        image = Image.open(image_path)
        # Görseli ekranda göster
        plt.imshow(image)
        plt.axis('off')  # Eksenleri kapat
        #plt.show()

    elif x_value == "8. Movement":
        showinfo('Camera angle', 'When choosing the video, make sure that it is like a camera angle in the image')
        image_path = 'C:/Users/kadir/PycharmProjects/denemeproject/Görseller/movement8_1.png'

        image = Image.open(image_path)
        # Görseli ekranda göster
        plt.imshow(image)
        plt.axis('off')  # Eksenleri kapat
        #plt.show()

    elif x_value == "9. Movement":
        showinfo('Camera angle', 'When choosing the video, make sure that it is like a camera angle in the image')
        image_path = 'C:/Users/kadir/PycharmProjects/denemeproject/Görseller/movement9_1.png'

        image = Image.open(image_path)
        # Görseli ekranda göster
        plt.imshow(image)
        plt.axis('off')  # Eksenleri kapat
        #plt.show()

    if image_path:
        try:
            image = Image.open(image_path)
            root.geometry('900x560')
            # Ekran çözünürlüğünüze veya istediğiniz boyuta göre ayarlayın
            screen_width = root.winfo_screenwidth()  # Ekran genişliğini al
            screen_height = root.winfo_screenheight()  # Ekran yüksekliğini al
            resized_image = image.resize((screen_width // 2, screen_height // 2), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(resized_image)
            label = Label(root, image=photo)
            label.image = photo  # Referansı sakla
            label.pack()
        except Exception as e:
            print(f"Picture Installation Error: {e}")
    else:
        print("Error: No valid file path was provided.")


def process_video(name, surname, x_value, y_value, phone, mail, doctor_ID, dosya_yolu, filename, target_reps):

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        cap = cv2.VideoCapture(filename)
        if not cap.isOpened():
            showerror(
                title='Video Error',
                message='Failed to open the video file. Please make sure it is a valid video file.'
            )
            return
        counter = 0
        stage = None

        output_dir = "output_files"
        os.makedirs(output_dir, exist_ok=True)

        movement_number = x_value.split('.')[0]
        # Yerel dosya yolu
        local_file_path = os.path.join(output_dir, f"{name}_{surname}_{movement_number}_{formatted_time}.txt")

        # Construct the output file path including the name and surname
        file_name = f"{name}_{surname}_{x_value}.motion"
        dosya_yolu = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)

        with open(dosya_yolu, 'w') as file, open(local_file_path, 'w') as local_file:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret or frame is None:
                    #Video frame'ini başarıyla okuyamadıysanız veya frame boşsa işlemi sonlandırın.
                    break
                    cap.release()
                    cv2.destroyAllWindows()
                    return
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = pose.process(image)
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                try:
                    landmarks = results.pose_landmarks.landmark
                    if y_value == 1:
                        shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                                    landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                        hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                               landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                        knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
                                landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
                    elif y_value == 2:
                        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                                    landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                        hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                               landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                        knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                                landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                    angle = calculate_angle(shoulder, hip, knee)

                    file.write(f"Angle: {round(angle, 2)} | Counter: {counter}\n")
                    local_file.write(f"Angle: {round(angle, 2)} | Counter: {counter}\n")
                    cv2.putText(image, f"Angle: {angle}",
                                tuple(np.multiply(hip, [840, 480]).astype(int)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
                    if angle > 160:
                        stage = "down"
                    if angle < 150 and stage == 'down':
                        stage = "up"
                        counter += 1
                except:
                    angle = 0
                    pass
                cv2.rectangle(image, (0, 0), (225, 73), (245, 117, 16), -1)
                cv2.putText(image, 'REPS', (15, 12),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                cv2.putText(image, str(counter),
                            (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                          mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                          mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
                                          )
                cv2.imshow('Motion Tracking Application', image)
                if cv2.waitKey(10) & 0xFF == ord('a'):
                    break

            cap.release()
            cv2.destroyAllWindows()

        # Karşılaştırma
        if counter != target_reps:
            showerror(
                title='Repetition Mismatch',
                message=f'The detected repetitions ({counter}) do not match the expected repetitions ({target_reps}).Information of your doctor'
            )
            return
        else:
            showinfo(
                title='Repetition Match',
                message=f'The detected repetitions ({counter}) match the expected repetitions ({target_reps}).'
            )

        def get_patient_subcollection_id(email):
            try:
                # Hasta alt koleksiyonunun ID'sini almak için Firestore sorgusunu yapın
                patient_ref = db.collection('Patients').where('mail', '==', email).limit(1)
                docs = patient_ref.stream()

                for doc in docs:
                    patient_data = doc.to_dict()
                    patient_id = doc.id  # Alt koleksiyon ID'sini alın
                    # Hasta ID'sini döndürün
                    return patient_id  # Buradaki indentation hatasını düzeltin
            except Exception as e:
                print(f"Error: {e}")
                return None  # Bir hata oluşursa `None` döndürün veya uygun bir hata işleme stratejisi kullanın

        movement_number = x_value.split('.')[0]
        patient_ID = get_patient_subcollection_id(mail)
        analyze_and_write_data(name,surname,doctor_ID,x_value,patient_ID, filename,dosya_yolu)

        video_path_on_cloud = f"{doctor_ID}/{patient_ID}/{Movements}/{movement_number}/{movement_number}_{formatted_time}.mp4"
        file_path_on_cloud = f"{doctor_ID}/{patient_ID}/{Movements}/{movement_number}/{movement_number}_{formatted_time}.txt"

        video_uploaded = False
        file_uploaded = False

        try:
            storage.child(video_path_on_cloud).put(filename)
            video_uploaded = True
        except Exception as e:
            showerror(
                title='Firebase Storage Error',
                message=f'Error uploading to Firebase Storage: {e}'
            )

        try:
            storage.child(file_path_on_cloud).put(dosya_yolu)
            file_uploaded = True
        except Exception as e:
            showerror(
                title='Firebase Storage Error',
                message=f'Error uploading to Firebase Storage: {e}'
            )

def analyze_and_write_data(name,surname,doctor_ID,x_value,patient_ID, filename,dosya_yolu):
    try:
        # Dosyanın içeriğini bir liste olarak tutmak için aç
        with open(dosya_yolu, 'r') as file:
            data = file.readlines()
        counter_angles = defaultdict(list)
        for line in data:
            angle = float(line.split('|')[0].split(':')[1].strip())
            counter = int(line.split('|')[1].split(':')[1].strip())
            counter_angles[counter].append(angle)
        result_array = []
        for counter, angles in counter_angles.items():
            min_angle = min(angles)
            max_angle = max(angles)
            result_array.extend([min_angle, max_angle])
        x = 1
        sum = 0
        diff_values = []
        with open(dosya_yolu, 'a') as file:
            for i in range(0, len(result_array) - 3, 2):
                diff = result_array[i + 1] - result_array[i + 2]
                diff_values.append(diff)
                file.write(f"{result_array[i + 1]} - {result_array[i + 2]} = {diff}\n")
                file.write(f"{x}. range of motion = {round(diff, 2)}\n")
                x += 1
            for j in range(0, len(diff_values), 1):
                sum = sum + diff_values[j]
            average = sum / len(diff_values)
            file.write(f"Avarege of total motion:{round(average,2)}\n")

            movement_number = x_value.split('.')[0]
            foto_path_on_cloud =f"{doctor_ID}/{patient_ID}/{Movements}/{movement_number}/{movement_number}_{formatted_time}"
            fig_width = max(10, len(diff_values) * 2)  # Minimum genişlik 10 inç olsun
            fig_height = 5
            x_labels = list(range(1, len(diff_values) + 1))
            plt.figure(figsize=(fig_width, fig_height))  # Dinamik boyutlandırma
            plt.plot( x_labels,diff_values,marker='o', linestyle='-', color='b')  # Çizgi grafiği çiz
            plt.title('Differences of Movement Intervals')  # Grafiğin başlığını ekle
            plt.xlabel('Measurement index')  # X ekseni başlığını ekle
            plt.ylabel('Difference value')  # Y ekseni başlığını ekle
            plt.grid(True)  # Izgara çizgilerini göster
            plt.savefig('numbers_graphic.png')
            plt.close()
            plt.show()  # Grafiği göster

            try:
                storage.child(foto_path_on_cloud).put('numbers_graphic.png')
                showinfo(
                    title='Process Completed',
                    message=f'All files saved and uploaded to Firebase Storage.'
                )
            except Exception as e:
                showerror(
                    title='Firebase Storage Error',
                    message=f'Error uploading to Firebase Storage: {e}'
                )


    except Exception as e:
        print(f'Error: {e}')  # Hata durumunda ayrıntılı çıktı sağlar
        showerror(
            title='Error',
            message=f'Error analyzing and writing data: {e}'
        )


def select_file(email):
    def process_video_wrapper(name, surname, phone, mail, doctor_ID):
        x_value = selected_x_value.get()
        if not x_value:
            showerror(
                title='Missing Information',
                message='Please select a movement.'
            )
            return
        if x_value in ["1. Movement", "3. Movement", "5. Movement", "6. Movement", "8. Movement", "9. Movement",]:
            y_value = 1
        elif x_value in ["2. Movement", "4. Movement", "7. Movement"]:
            y_value = 2
        else:
            showerror(
                title='Invalid Input',
                message='Please select a movement.'
            )
            return

        try:
            target_reps = int(reps_entry.get())
        except ValueError:
            showerror(
                title='Invalid Input',
                message='Please enter a valid number for repetitions.'
            )
            return

        selected_value_label.config(text=f'Selected Leg: {y_value}')
        show_movement_info(x_value, root)  # Seçilen hareket türüne göre bilgi göster
        root.update()  # Tkinter ana döngüsünü güncelle
        filename = fd.askopenfilename(
            title='Select a Video',
            initialdir='/',
            filetypes=(('video files', '*.mp4'), ('video files', '*.mov'))
        )
        if not filename:
            # Kullanıcı dosya seçim penceresini kapattıysa veya bir dosya seçmediyse işlemi sonlandırın.
            return

        showinfo(
            title='Selected File',
            message=filename
        )
        dosya_adi = f"{name}_{surname}_{x_value}.motion.txt"
        dosya_yolu = os.path.join(os.path.dirname(os.path.abspath(__file__)), dosya_adi)
        process_video(name, surname, x_value, y_value, phone, mail, doctor_ID, dosya_yolu, filename, target_reps)

    def get_user_info_from_db(email):
        # Remove 'nonlocal email' since it's not nested within another function
        name, surname, phone, doctor_ID, mail = "", "", "", "", email  # Initialize variables
        # Fetch user information from the Firestore database
        user_ref = db.collection('Patients').where('mail', '==', mail).limit(1)
        docs = user_ref.stream()

        for doc in docs:
            user_data = doc.to_dict()
            name = user_data.get('name', '')
            surname = user_data.get('surname', '')
            phone = str(user_data.get('phone', ''))
            doctor_ID = str(user_data.get('doctor_ID', ''))
            mail = user_data.get('mail', '')
            break  # Stop loop after fetching the first matching document
        return name, surname, phone, mail, doctor_ID  # Return fetched user information

    # Initialize tkinter window and fetch user information
    input_window = tk.Toplevel(root)
    input_window.title('Input Value')
    input_window.geometry('479x359')
    input_window.resizable(False, False)

    global bg_image
    bg_image = tk.PhotoImage(file="resim.png")
    background_label = tk.Label(input_window, image=bg_image)
    background_label.place(relwidth=1, relheight=1)

    name, surname, phone, mail, doctor_ID = get_user_info_from_db(email)  # Fetch user information from the database

    x_label = ttk.Label(input_window, text='Select the movement:')
    x_label.pack()
    x_values = [" ", "1. Movement", "2. Movement", "3. Movement", "4. Movement", "5. Movement", "6. Movement",
                "7. Movement", "8. Movement", "9. Movement"]
    selected_x_value = tk.StringVar()
    selected_x_value.set(x_values[0])
    x_menu = ttk.OptionMenu(input_window, selected_x_value, *x_values)
    x_menu.pack()

    reps_label = ttk.Label(input_window, text='Enter the number of repetitions:')
    reps_label.pack()
    reps_entry = ttk.Entry(input_window)
    reps_entry.pack()

    start_button = ttk.Button(
        input_window,
        text='Start Processing',
        command=lambda: process_video_wrapper(name, surname, phone, mail, doctor_ID)
        # Fonksiyona parametreleri # iletiliyor
    )
    start_button.pack()

    selected_value_label = ttk.Label(input_window, text="")
    selected_value_label.pack()


root = tk.Tk()
root.title('Motion Tracking Application')
root.resizable(False, False)
root.geometry('479x359')

bg = tk.PhotoImage(file="resim.png")
label1 = tk.Label(root, image=bg)
label1.place(x=0, y=0)

# Sign In button
login_button = tk.Button(root, text="Log In", command=login)
login_button.place(x=150, y=150)

# Sign Up button
register_button = tk.Button(root, text="Sign Up", command=register)
register_button.place(x=300, y=150)

root.mainloop()
