import rospy
import os
import rospkg
import subprocess

from gazebo_msgs.msg import ModelState
from gazebo_msgs.srv import SetModelState, DeleteModel, SpawnModel, SpawnModelRequest, DeleteModelRequest

from geometry_msgs.msg import Pose, PoseStamped, Point, Quaternion

from std_msgs.msg import Empty
from std_srvs.srv import Empty


from task_generator.simulators.simulator_factory import SimulatorFactory
from tf.transformations import quaternion_from_euler
from task_generator.constants import Constants
from task_generator.simulators.base_simulator import BaseSimulator
from task_generator.simulators.simulator_factory import SimulatorFactory

from task_generator.shared import ModelType, Obstacle, ObstacleProps, Robot


T = Constants.WAIT_FOR_SERVICE_TIMEOUT


@SimulatorFactory.register(Constants.Simulator.GAZEBO)
class GazeboSimulator(BaseSimulator):
    def __init__(self, namespace: str):

        super().__init__(namespace)
        self._goal_pub = rospy.Publisher(self._ns_prefix(
            "/goal"), PoseStamped, queue_size=1, latch=True)
        self._robot_name = rospy.get_param("robot_model", "")

        rospy.wait_for_service("/gazebo/spawn_urdf_model")
        rospy.wait_for_service("/gazebo/spawn_sdf_model")
        rospy.wait_for_service("/gazebo/set_model_state")
        rospy.wait_for_service("/gazebo/set_model_state", timeout=20)

        self._spawn_model[ModelType.URDF] = rospy.ServiceProxy(
            self._ns_prefix("gazebo", "spawn_urdf_model"), SpawnModel
        )
        self._spawn_model[ModelType.SDF] = rospy.ServiceProxy(
            self._ns_prefix("gazebo", "spawn_sdf_model"), SpawnModel
        )
        self._move_model_srv = rospy.ServiceProxy(
            "/gazebo/set_model_state", SetModelState, persistent=True
        )
        self.unpause = rospy.ServiceProxy("/gazebo/unpause_physics", Empty)
        self.pause = rospy.ServiceProxy("/gazebo/pause_physics", Empty)

        rospy.loginfo("Waiting for gazebo services...")
        rospy.wait_for_service("gazebo/spawn_sdf_model")
        rospy.wait_for_service("gazebo/delete_model")

        rospy.loginfo("service: spawn_sdf_model is available ....")
        self.remove_model_srv = rospy.ServiceProxy(
            "gazebo/delete_model", DeleteModel)

    def before_reset_task(self):
        self.pause()

    def after_reset_task(self):
        self.unpause()

    # ROBOT

    def move_robot(self, pos, name=None):
        model_state_request = ModelState()
        model_state_request.model_name = name if name else self._robot_name
        pose = Pose()
        pose.position.x = pos[0]
        pose.position.y = pos[1]
        pose.position.z = 0.35
        pose.orientation = Quaternion(
            *quaternion_from_euler(0.0, 0.0, pos[2], axes="sxyz")
        )
        model_state_request.pose = pose
        model_state_request.reference_frame = "world"

        self._move_model_srv(model_state_request)

    def spawn_robot(self, robot: Robot):
        request = SpawnModelRequest()

        robot_namespace = robot.namespace

        model = robot.model.get(self.MODEL_TYPES)
        
        rospy.set_param(os.path.join(robot_namespace,
                        "robot_description"), model.description)
        rospy.set_param(os.path.join(robot_namespace,
                        "tf_prefix"), robot_namespace)

        request.model_name = robot_namespace
        request.model_xml = model.description
        request.robot_namespace = robot_namespace
        request.reference_frame = "world"

        self.spawn_model(model.type, request)

        return robot.name

    def spawn_obstacle(self, obstacle):
        request = SpawnModelRequest()

        model = obstacle.model.get(self.MODEL_TYPES)

        request.model_name = obstacle.name
        request.model_xml = model.description
        request.initial_pose = Pose(
            position=Point(x=obstacle.position[0], y=obstacle.position[1], z=0),
            orientation=Quaternion(x=0, y=0, z=obstacle.position[2], w=1)
        )
        request.robot_namespace = self._ns_prefix(obstacle.name)
        request.reference_frame = "world"

        self.spawn_model(model.type, request)

        return obstacle.name

    def delete_obstacle(self, obstacle_id: str):
        self.remove_model_srv(DeleteModelRequest(model_name=obstacle_id))

    def _publish_goal(self, goal):
        goal_msg = PoseStamped()
        goal_msg.header.seq = 0
        goal_msg.header.stamp = rospy.get_rostime()
        goal_msg.header.frame_id = "map"
        goal_msg.pose.position.x = goal[0]
        goal_msg.pose.position.y = goal[1]

        goal_msg.pose.orientation.w = 0
        goal_msg.pose.orientation.x = 0
        goal_msg.pose.orientation.y = 0
        goal_msg.pose.orientation.z = 1

        self._goal_pub.publish(goal_msg)