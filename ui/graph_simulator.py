import math
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class ForceLayoutSimulator(QObject):
    """
    Obsidian-style Force-Directed Graph Layout Simulator for KnowledgeScene.
    Applies Coulomb's law repulsion between nodes, Hooke's spring attraction along edges,
    and soft center gravity with damping so nodes settle smoothly into an organic mind-map tree.
    """

    stepped = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.timer = QTimer(self)
        self.timer.setInterval(16)  # ~60 FPS
        self.timer.timeout.connect(self._step)

        # Physics tuning parameters
        self.k_repulse = 80000.0       # Repulsion strength
        self.k_spring = 0.006          # Edge spring attraction
        self.desired_edge_len = 260.0  # Ideal distance between connected nodes
        self.damping = 0.82            # Velocity drag
        self.center_gravity = 0.0008   # Pull towards scene center (0, 0)
        self.min_energy_threshold = 0.2

        self.velocities = {}
        self.iterations = 0
        self.max_iterations = 180

    def is_running(self) -> bool:
        return self.timer.isActive()

    def start(self, max_iterations=180):
        if not self.scene or len(self.scene.nodes) < 2:
            return
        self.max_iterations = max_iterations
        self.iterations = 0
        self.velocities = {nid: [0.0, 0.0] for nid in self.scene.nodes.keys()}
        self.scene.push_undo_state()
        self.timer.start()

    def stop(self):
        if self.timer.isActive():
            self.timer.stop()
            self.scene.save_data()
            self.finished.emit()

    def _step(self):
        if not self.scene or self.iterations >= self.max_iterations:
            self.stop()
            return

        nodes = self.scene.nodes
        edges = self.scene.edges

        # Ensure all existing nodes have velocity entries
        for nid in nodes.keys():
            if nid not in self.velocities:
                self.velocities[nid] = [0.0, 0.0]

        self.iterations += 1
        node_keys = list(nodes.keys())
        total_energy = 0.0

        # 1. Repulsion between all pairs of nodes (O(N^2) for clean layout)
        for i in range(len(node_keys)):
            k1 = node_keys[i]
            n1 = nodes[k1]
            pos1 = n1.pos()
            for j in range(i + 1, len(node_keys)):
                k2 = node_keys[j]
                n2 = nodes[k2]
                pos2 = n2.pos()

                dx = pos2.x() - pos1.x()
                dy = pos2.y() - pos1.y()
                dist_sq = dx * dx + dy * dy + 400.0
                dist = math.sqrt(dist_sq)

                force = self.k_repulse / dist_sq
                fx = (dx / dist) * force
                fy = (dy / dist) * force

                self.velocities[k1][0] -= fx
                self.velocities[k1][1] -= fy
                self.velocities[k2][0] += fx
                self.velocities[k2][1] += fy

        # 2. Hooke's spring attraction along edges
        for edge in edges:
            if edge.source_node and edge.target_node:
                s_id = edge.source_node.node_id
                t_id = edge.target_node.node_id
                if s_id not in self.velocities or t_id not in self.velocities:
                    continue

                p1 = edge.source_node.pos()
                p2 = edge.target_node.pos()
                dx = p2.x() - p1.x()
                dy = p2.y() - p1.y()
                dist = math.hypot(dx, dy)
                if dist < 0.1:
                    continue

                disp = dist - self.desired_edge_len
                force = disp * self.k_spring
                fx = (dx / dist) * force
                fy = (dy / dist) * force

                self.velocities[s_id][0] += fx
                self.velocities[s_id][1] += fy
                self.velocities[t_id][0] -= fx
                self.velocities[t_id][1] -= fy

        # 3. Apply velocities, damping, and central gravity
        for nid, node in nodes.items():
            if node.isSelected() or getattr(node, "_is_resizing", False):
                # Don't move a node currently being dragged/selected by user
                self.velocities[nid] = [0.0, 0.0]
                continue

            vx, vy = self.velocities[nid]
            pos = node.pos()

            # Gentle center attraction
            vx += -pos.x() * self.center_gravity
            vy += -pos.y() * self.center_gravity

            vx *= self.damping
            vy *= self.damping

            # Cap speed to avoid jerky movement
            speed = math.hypot(vx, vy)
            if speed > 40.0:
                vx = (vx / speed) * 40.0
                vy = (vy / speed) * 40.0

            node.setPos(pos.x() + vx, pos.y() + vy)
            total_energy += speed
            self.velocities[nid] = [vx, vy]

        self.scene.update_edges()
        self.stepped.emit()

        # Stop early if equilibrium reached
        if total_energy < self.min_energy_threshold:
            self.stop()
