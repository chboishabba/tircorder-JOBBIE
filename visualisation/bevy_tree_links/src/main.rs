use bevy::prelude::*;
use bevy_tweening::{lens::*, *};
use std::time::Duration;

/// Marker component for spawned nodes.
#[derive(Component)]
struct Node;

/// Component storing parent and child entities for a link.
#[derive(Component)]
struct Link {
    parent: Entity,
    child: Entity,
}

/// Animated progress of a link from 0.0 to 1.0.
#[derive(Component, Deref, DerefMut)]
struct LinkProgress(f32);

/// Lens to animate `LinkProgress` with `bevy_tweening`.
struct LinkProgressLens;

impl Lens<LinkProgress> for LinkProgressLens {
    fn lerp(&mut self, target: &mut LinkProgress, ratio: f32) {
        target.0 = ratio;
    }
}

fn main() {
    App::new()
        .add_plugins(DefaultPlugins)
        .add_plugin(TweeningPlugin)
        .add_startup_system(setup)
        .add_system(update_links)
        .run();
}

/// Spawn sample nodes and a cylinder link between them.
fn setup(
    mut commands: Commands,
    mut meshes: ResMut<Assets<Mesh>>,
    mut materials: ResMut<Assets<StandardMaterial>>,
) {
    // Camera
    commands.spawn(Camera3dBundle::default());

    // Parent node at origin
    let parent = commands
        .spawn((
            PbrBundle {
                mesh: meshes.add(shape::UVSphere::default().into()),
                material: materials.add(Color::WHITE.into()),
                ..default()
            },
            Node,
        ))
        .id();

    // Child node offset on the X axis
    let child = commands
        .spawn((
            PbrBundle {
                mesh: meshes.add(shape::UVSphere::default().into()),
                material: materials.add(Color::BLUE.into()),
                transform: Transform::from_xyz(2.0, 0.0, 0.0),
                ..default()
            },
            Node,
        ))
        .id();

    // Link using a cylinder mesh. Start with zero length and animate to full.
    let tween = Tween::new(
        EaseFunction::QuadraticOut,
        Duration::from_secs(1),
        LinkProgressLens,
    );

    commands
        .spawn((
            PbrBundle {
                mesh: meshes.add(
                    shape::Cylinder {
                        height: 1.0,
                        radius: 0.02,
                        ..default()
                    }
                    .into(),
                ),
                material: materials.add(Color::BLACK.into()),
                ..default()
            },
            Link { parent, child },
            LinkProgress(0.0),
            Animator::new(tween),
        ));
}

/// Update link transforms when nodes move.
fn update_links(
    mut link_query: Query<(&Link, &LinkProgress, &mut Transform)>,
    node_query: Query<&Transform, With<Node>>,
) {
    for (link, progress, mut transform) in &mut link_query {
        if let (Ok(parent_tf), Ok(child_tf)) =
            (node_query.get(link.parent), node_query.get(link.child))
        {
            let delta = child_tf.translation - parent_tf.translation;
            let length = delta.length();

            transform.translation = parent_tf.translation + delta * 0.5;
            transform.rotation = Quat::from_rotation_arc(Vec3::Y, delta.normalize());
            transform.scale = Vec3::new(1.0, length * 0.5 * progress.0, 1.0);
        }
    }
}
