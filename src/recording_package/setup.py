from setuptools import find_packages, setup

package_name = "recording_package"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/video_recorder.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="robot007",
    maintainer_email="robot007@example.com",
    description="ROS 2 camera video recording package with command and test interfaces.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "video_recorder = recording_package.video_recorder:main",
            "recording_test_client = recording_package.recording_test_client:main",
        ],
    },
)
