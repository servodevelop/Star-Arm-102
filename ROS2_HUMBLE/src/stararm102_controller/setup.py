from setuptools import setup

package_name = 'stararm102_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nyancos',
    maintainer_email='12461360+nyancos@user.noreply.gitee.com',
    description='Controller package for StarArm 102 robot',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'stararm102_controller = stararm102_controller.stararm102_controller:main',
        ],
    },
)
