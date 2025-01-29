import cv2
import os

# Kullanıcıdan resimlerin bulunduğu klasör yolunu al
folder_path = input("Lütfen resimlerin bulunduğu klasörün yolunu girin: ")

# Klasördeki tüm resim dosyalarını listele
image_files = [f for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp",".webp",".avif"))]

# Resim dosyalarını listele ve kullanıcıya seçme imkanı ver
if not image_files:
    print("Klasörde hiçbir resim bulunamadı!")
    exit()

print("Klasördeki resimler:")
for i, file_name in enumerate(image_files, start=1):
    print(f"{i}: {file_name}")

# Kullanıcıdan bir resim seçmesini iste
while True:
    try:
        selection = int(input("Lütfen işlem yapmak istediğiniz resmin numarasını girin: "))
        if 1 <= selection <= len(image_files):
            break
        else:
            print("Geçerli bir sayı giriniz.")
    except ValueError:
        print("Lütfen geçerli bir sayı giriniz.")

# Seçilen resmi yükle
selected_image_path = os.path.join(folder_path, image_files[selection - 1])
selected_image_name = os.path.splitext(image_files[selection - 1])[0]
image = cv2.imread(selected_image_path)
original_image = image.copy()
original_height, original_width = image.shape[:2]

# Zoom ve kaydırma için değişkenler
scale = 1.0
scroll_x, scroll_y = 0, 0
left_border, top_border = 0, 0

# Seçim listesi
roi_list = []

# Fare olayları için global değişkenler
start_x, start_y, selecting = -1, -1, False

def resize_and_center_image(image, window_width, window_height):
    """Görüntüyü pencereye sığacak şekilde boyutlandırır ve ortalar."""
    h, w = image.shape[:2]
    scale = min(window_width / w, window_height / h)
    resized_image = cv2.resize(image, (int(w * scale), int(h * scale)))

    top_border = (window_height - resized_image.shape[0]) // 2
    bottom_border = window_height - resized_image.shape[0] - top_border
    left_border = (window_width - resized_image.shape[1]) // 2
    right_border = window_width - resized_image.shape[1] - left_border

    centered_image = cv2.copyMakeBorder(resized_image, top_border, bottom_border, left_border, right_border, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    return centered_image, scale, left_border, top_border

def handle_mouse_events(event, x, y, flags, param):
    """Mouse olaylarını yönetir (seçim ve zoom)."""
    global start_x, start_y, selecting, roi_list, scale, left_border, top_border, image

    if event == cv2.EVENT_LBUTTONDOWN:
        start_x, start_y = int((x - left_border) / scale), int((y - top_border) / scale)
        selecting = True

    elif event == cv2.EVENT_MOUSEMOVE and selecting:
        temp_image = image.copy()
        end_x, end_y = int((x - left_border) / scale), int((y - top_border) / scale)
        cv2.rectangle(temp_image, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
        display_image, _, _, _ = resize_and_center_image(temp_image, window_width, window_height)
        cv2.imshow("Resizable Image", display_image)

    elif event == cv2.EVENT_LBUTTONUP:
        selecting = False
        end_x, end_y = int((x - left_border) / scale), int((y - top_border) / scale)

        # Koordinatları normalize et
        start_x, end_x = sorted([start_x, end_x])
        start_y, end_y = sorted([start_y, end_y])

        if start_x < 0 or start_y < 0 or end_x > original_width or end_y > original_height:
            print(f"Geçersiz seçim: ({start_x}, {start_y}) - ({end_x}, {end_y})")
            return
        roi_list.append((start_x, start_y, end_x, end_y))
        cv2.rectangle(image, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
        display_image, _, _, _ = resize_and_center_image(image, window_width, window_height)
        cv2.imshow("Resizable Image", display_image)

    elif event == cv2.EVENT_MOUSEWHEEL:
        if flags > 0:  # Zoom in
            scale = min(scale + 0.1, 5.0)
        else:  # Zoom out
            scale = max(scale - 0.1, 0.1)
        image = cv2.resize(original_image, (int(original_width * scale), int(original_height * scale)))

# Monitör çözünürlüğünü belirleme
window_width = 1920
window_height = 1080

# Pencereyi oluştur ve her zaman üstte olacak şekilde ayarla
cv2.namedWindow("Resizable Image", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Resizable Image", window_width, window_height)
cv2.setWindowProperty("Resizable Image", cv2.WND_PROP_TOPMOST, 1)
cv2.setMouseCallback("Resizable Image", handle_mouse_events)

print("Seçim yapmak için sol tıklayın ve sürükleyin. Yakınlaştırma/uzaklaştırma için fare tekerleğini kullanın. İşiniz bittiğinde 'q' tuşuna basın.")

while True:
    display_image, scale, left_border, top_border = resize_and_center_image(image, window_width, window_height)
    cv2.imshow("Resizable Image", display_image)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cv2.destroyAllWindows()

# Seçilen bölgeleri kaydet
output_folder = os.path.join(folder_path, selected_image_name)
os.makedirs(output_folder, exist_ok=True)

for i, (start_x, start_y, end_x, end_y) in enumerate(roi_list):
    if start_x < 0 or start_y < 0 or end_x > original_width or end_y > original_height or start_x >= end_x or start_y >= end_y:
        print(f"Geçersiz seçim kaydedilmedi: ({start_x}, {start_y}) - ({end_x}, {end_y})")
        continue
    roi = original_image[start_y:end_y, start_x:end_x]
    output_path = os.path.join(output_folder, f"roi_{i + 1}.jpg")
    cv2.imwrite(output_path, roi)
    print(f"Bölge {i + 1} kaydedildi: {output_path}")