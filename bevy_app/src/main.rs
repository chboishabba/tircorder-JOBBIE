use bevy::core_pipeline::prelude::Camera3dBundle;
use bevy::pbr::prelude::PbrBundle;
use bevy::prelude::*;
use bevy_mod_picking::DefaultPickingPlugins;
use bevy_mod_picking::prelude::PickableBundle;

fn main() {
    App::new()
        .add_plugins((DefaultPlugins, DefaultPickingPlugins))
        .add_systems(Startup, setup)
        .run();
}

fn setup(
    mut commands: Commands,
    mut meshes: ResMut<Assets<Mesh>>,
    mut materials: ResMut<Assets<StandardMaterial>>,
) {
    commands.spawn(Camera3dBundle {
        transform: Transform::from_xyz(0.0, 0.0, 5.0).looking_at(Vec3::ZERO, Vec3::Y),
        ..default()
    });

    commands.spawn((
        PbrBundle {
            mesh: meshes.add(Cuboid::new(2.0, 1.0, 0.1)),
            material: materials.add(Color::srgb(0.96, 0.96, 0.96)),
            transform: Transform::from_translation(Vec3::ZERO),
            ..default()
        },
        PickableBundle::default(),
    ));
}
