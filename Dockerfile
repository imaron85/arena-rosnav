# Main Dockerfile

FROM osrf/ros:noetic-desktop-full

SHELL ["/bin/bash", "-c"]

# Install Deps
RUN apt-get update -y && apt install -y python3 python-is-python3 git python3-rosdep python3-pip python3-rosinstall python3-rosinstall-generator python3-wstool build-essential

# Install Poetry
RUN pip3 install poetry && pip3 install --upgrade pip

RUN pip install torch rospkg PyYAML filelock scipy PyQT5 empy defusedxml wandb lxml seaborn netifaces

RUN mkdir -p /root/src/
WORKDIR /root/src/
RUN git clone https://github.com/Arena-Rosnav/arena-rosnav.git
WORKDIR /root/src/arena-rosnav

RUN apt install -y libopencv-dev liblua5.2-dev ros-noetic-navigation ros-noetic-teb-local-planner ros-noetic-mpc-local-planner libarmadillo-dev ros-noetic-nlopt ros-noetic-turtlebot3-description ros-noetic-turtlebot3-navigation ros-noetic-lms1xx ros-noetic-velodyne-description ros-noetic-hector-gazebo ros-noetic-ira-laser-tools liblcm-dev

RUN echo -e "source /opt/ros/noetic/setup.sh" >> /root/.bashrc
RUN echo -e "source /root/devel/setup.sh" >> /root/.bashrc

WORKDIR /root/src/arena-rosnav
RUN rosws update

WORKDIR /root/
RUN source /root/.bashrc \
    && source /opt/ros/noetic/setup.sh \
    && catkin_make