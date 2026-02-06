from ursina import *
from multiprocessing import Process, Queue, shared_memory
import struct

class UrsinaViewer:
    def __init__(self, queue):
        self.app = Ursina()
        self.queue = queue

        self.audio = None
        self.audio_path = None

        try:
            self.shm = shared_memory.SharedMemory(name="shm_3D")
            self.buffer = self.shm.buf
        except FileNotFoundError:
            print("Erreur : Segment 'shm_3D' introuvable. Lancez le script producteur d'abord.")
            self.buffer = None

        self.center = Entity()
        camera.parent = self.center
        camera.position = (0, 15, -30)
        camera.look_at(self.center)

        window.color = color.black
        window.borderless = True
        window.exit_button.enabled = False
        window.fps_counter.enabled = False 
        window.collider_counter.enabled = False
        window.entity_counter.enabled = False
        window.fullscreen = True
        window.always_on_top = True

        self.model = Entity(model="cube",scale=2, position=(0, 0, 0))

        self.controller = Entity()
        self.controller.update = self.update_logic

    def update_logic(self):
        
        if self.buffer:
            try:
                rot_raw = struct.unpack("f", self.buffer[0:4])[0]
                self.center.rotation_y = round(rot_raw, 2)
            except Exception as e:
                print(f"Erreur SHM : {e}")

        while not self.queue.empty():
            try:
                cmd, value = self.queue.get_nowait()

                if cmd == "set_project":
                    project_path = Path("content") / value["project"]
                    
                    for f in project_path.iterdir():
                        if f.suffix.lower() in [".glb", ".glbf"]:
                            self.model.model = load_model(str(f)) 
                            bounds = self.model.model_bounds
                            max_dim = max(bounds.size)
                            center = bounds.center
                            self.model.origin = center
                            if max_dim > 0:
                                target_size = 5
                                self.model.scale = target_size / max_dim
                            self.model.position = (0, 0, 0)
                            break


                    audio_path = project_path / f"{value['language']}.wav"

                    if not audio_path.exists():
                        self.audio = None
                        self.audio_path = None
                    else:
                        self.audio_path = audio_path


                elif cmd == "play_audio":
                    if self.audio:
                        self.audio.stop()

                    if self.audio_path:
                        self.audio = Audio(str(self.audio_path), loop=False, autoplay=True)
                    
            except Exception as e:
                print(f"Erreur Queue : {e}")

    def run(self):
        self.app.run()

def start_viewer(queue):
    viewer = UrsinaViewer(queue)
    viewer.run()

if __name__ == "__main__":
    q = Queue()
    
    p = Process(target=start_viewer, args=(q,))
    p.start()

    q.put(("set_model","content//test2//test5.glb"))

    p.join()

