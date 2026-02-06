from multiprocessing import Queue, shared_memory
import struct
import cv2
import math



def face_detection(buffer_track,queue,camera_index=0):

    face_cascade_path = "haarcascade_frontalface_default.xml"
    palm_cascade_path = "palm.xml"

    face_cascade = cv2.CascadeClassifier(face_cascade_path)
    palm_cascade = cv2.CascadeClassifier(palm_cascade_path)

    cap = cv2.VideoCapture(camera_index)

    previous_faces = []
    previous_palms = []

    next_face_id = 0 
    next_palm_id = 0          

    def distance(p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])
    
    def calculate_rot(cx,w):
        cw = w / 2
        rot = (cx - cw) / cw
        rot = max(-1, min(1, rot))
        return round(rot, 2)
    
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Erreur : impossible de lire la caméra.")
            break

        height, width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)
        palms = palm_cascade.detectMultiScale(gray, 1.2, 5)

        current_faces = []
        current_palms = []

        for (x, y, w, h) in faces:
            cx = x + w // 2
            cy = y + h // 2

            assigned_id = None

            # --- Matching avec les anciens centres ---
            for old in previous_faces:
                if distance((cx, cy), (old["cx"], old["cy"])) < 50:
                    assigned_id = old["id"]
                    break

            # Si aucun ancien visage ne correspond → nouveau visage
            if assigned_id is None:
                assigned_id = next_face_id
                next_face_id += 1

            current_faces.append({"id": assigned_id, "cx": cx, "cy": cy, "bbox": (x, y, w, h)})
        
        current_faces.sort(key=lambda f: f["bbox"][2] * f["bbox"][3], reverse=True)

        for (x, y, w, h) in palms:
            cx = x + w // 2
            cy = y + h // 2

            assigned_id = None
            lifetime = 0

            # --- Matching avec les anciens centres ---
            for old in previous_palms:
                if distance((cx, cy), (old["cx"], old["cy"])) < 50:
                    assigned_id = old["id"]
                    lifetime = old["lifetime"] + 1
                    if lifetime == 15:
                        queue.put(("play_audio", None))
                    break

            # Si aucun ancien visage ne correspond → nouveau visage
            if assigned_id is None:
                assigned_id = next_palm_id
                next_palm_id += 1

            current_palms.append({"id": assigned_id, "cx": cx, "cy": cy, "bbox": (x, y, w, h),"lifetime": lifetime})
        
        current_faces.sort(key=lambda f: f["bbox"][2] * f["bbox"][3], reverse=True)

        # --- Affichage console ---
        if current_faces:
            buffer_track[:] = struct.pack("f", calculate_rot(current_faces[0]["cx"], width))
        else:
            buffer_track[:] = struct.pack("f", 0.0)


        # --- Dessin ---
        for f in current_faces:
            x, y, w, h = f["bbox"]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
            cv2.putText(frame, f"ID {f['id']}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
            cv2.circle(frame, (f["cx"], f["cy"]), 5, (0,0,255), -1)

        for f in current_palms:
            x, y, w, h = f["bbox"]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255,0,0), 2)
            cv2.putText(frame, f"ID {f['id']} L:{f['lifetime']}", (x, y - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)
            cv2.circle(frame, (f["cx"], f["cy"]), 5, (0,0,255), -1)

        cv2.imshow("Detection continue", frame)

        # Mise à jour pour la prochaine frame
        previous_faces = current_faces
        previous_palms = current_palms

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        shm = shared_memory.SharedMemory(name='shm_track')
        shm.close()
        shm.unlink()
        print("Mémoire shm_track supprimée.")
    except FileNotFoundError:
        print("Aucune mémoire shm_track à supprimer.")

    shm_track = shared_memory.SharedMemory(create=True, size=4, name='shm_track')
    buffer = shm_track.buf

    face_detection(buffer)