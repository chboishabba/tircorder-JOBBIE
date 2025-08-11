use bevy::prelude::*;
use bevy::sprite::MaterialMesh2dBundle;
use bevy_text_mesh::prelude::*;

fn main() {
    App::new()
        .add_plugins(DefaultPlugins)
        .add_plugins(TextMeshPlugin)
        .add_systems(Startup, setup)
        .run();
}

/// Set up the camera and spawn an example speech bubble.
fn setup(
    mut commands: Commands,
    mut meshes: ResMut<Assets<Mesh>>,
    mut materials: ResMut<Assets<ColorMaterial>>,
    asset_server: Res<AssetServer>,
) {
    commands.spawn(Camera2dBundle::default());

    spawn_speech_bubble(
        &mut commands,
        &mut meshes,
        &mut materials,
        &asset_server,
        "Hello, Bevy!",
        Vec3::ZERO,
        true,
    );
}

/// Spawn a Facebook-style speech bubble with rounded corners, text, a shadow,
/// and an optional tail.
///
/// Returns the entity id of the main bubble mesh.
pub fn spawn_speech_bubble(
    commands: &mut Commands,
    meshes: &mut Assets<Mesh>,
    materials: &mut Assets<ColorMaterial>,
    asset_server: &AssetServer,
    text: &str,
    position: Vec3,
    with_tail: bool,
) -> Entity {
    let bubble_shape = shapes::RoundedRectangle {
        width: 250.0,
        height: 100.0,
        radius: Vec4::splat(12.0),
        ..default()
    };

    let shadow_mesh = meshes.add(Mesh::from(bubble_shape.clone()));
    let bubble_mesh = meshes.add(Mesh::from(bubble_shape));

    // drop shadow
    commands.spawn((
        MaterialMesh2dBundle {
            mesh: shadow_mesh.clone().into(),
            material: materials.add(Color::rgba(0.0, 0.0, 0.0, 0.2).into()),
            transform: Transform::from_translation(position + Vec3::new(5.0, -5.0, -0.1)),
            ..default()
        },
    ));

    // main bubble
    let bubble_entity = commands
        .spawn((
            MaterialMesh2dBundle {
                mesh: bubble_mesh.into(),
                material: materials.add(Color::rgb(0.96, 0.96, 0.96).into()),
                transform: Transform::from_translation(position),
                ..default()
            },
        ))
        .id();

    // optional tail
    if with_tail {
        commands.spawn((
            MaterialMesh2dBundle {
                mesh: meshes
                    .add(Mesh::from(shapes::RegularPolygon {
                        sides: 3,
                        feature: shapes::RegularPolygonFeature::Radius(15.0),
                        ..default()
                    }))
                    .into(),
                material: materials.add(Color::rgb(0.96, 0.96, 0.96).into()),
                transform: Transform {
                    translation: position + Vec3::new(-80.0, -40.0, 0.0),
                    rotation: Quat::from_rotation_z(std::f32::consts::PI / 2.0),
                    ..default()
                },
                ..default()
            },
        ));
    }

    // text
    commands.spawn(Text2dBundle {
        text: Text::from_section(
            text,
            TextStyle {
                font: asset_server.load("fonts/FiraSans-Bold.ttf"),
                font_size: 28.0,
                color: Color::BLACK,
            },
        )
        .with_justify(JustifyText::Center),
        transform: Transform::from_translation(position + Vec3::new(0.0, 0.0, 0.1)),
        ..default()
    });

    bubble_entity
}

