from setuptools import find_packages, setup
from glob import glob

package_name = 'stararm102_gazebo'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name+'/config/', glob('config/*.xacro')),
        ('share/' + package_name+'/launch/', glob('launch/*.py')),
        ('share/' + package_name+'/urdf/', glob('urdf/*')),
        ('share/' + package_name+'/meshes', glob('meshes/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nyancos',
    maintainer_email='12461360+nyancos@user.noreply.gitee.com',
    description='Gazebo simulation package for StarArm 102',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)
