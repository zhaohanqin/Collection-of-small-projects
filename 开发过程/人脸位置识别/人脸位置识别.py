import cv2
import mediapipe as mp

mp_face_detection = mp.solutions.face_detection

cap = cv2.VideoCapture(0)

# 创建人脸检测器
with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(image_rgb)

        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                h, w, _ = frame.shape
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)

                # ✅ 改进：扩大框的大小
                expand_ratio = 0.3  # 向上和四周扩展 30%
                x_new = max(int(x - width * expand_ratio * 0.5), 0)
                y_new = max(int(y - height * expand_ratio), 0)
                w_new = min(int(width * (1 + expand_ratio)), w - x_new)
                h_new = min(int(height * (1 + expand_ratio)), h - y_new)

                # 画扩大后的矩形框
                cv2.rectangle(frame, (x_new, y_new), (x_new + w_new, y_new + h_new), (0, 255, 0), 2)

        cv2.imshow('Face + Head Detection (Expanded)', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
