from setuptools import find_packages, setup
from glob import glob

package_name = 'viola_gazebo'

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
        # ('share/' + package_name+'/rviz/', glob('rviz/*')),
        ('share/' + package_name+'/meshes', glob('meshes/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nyancos',
    maintainer_email='12461360+nyancos@user.noreply.gitee.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)
