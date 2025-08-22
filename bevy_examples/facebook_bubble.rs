use bevy::prelude::*;
use bevy::sprite::MaterialMesh2dBundle;
use bevy_mod_picking::prelude::*;
use bevy_text_mesh::prelude::*;

/// Stores the speech bubbles spawned for a parent entity.
#[derive(Component, Default)]
struct BubbleChildren(Vec<Entity>);

/// Controls target scale and highlight state for a bubble.
#[derive(Component)]
struct BubbleAnimation {
    /// Desired scale for the bubble.
    target_scale: Vec3,
    /// Whether the bubble is highlighted.
    highlight: bool,
}

impl Default for BubbleAnimation {
    fn default() -> Self {
        Self {
            target_scale: Vec3::ONE,
            highlight: false,
        }
    }
}

/// Associates a bubble with a media entity.
#[derive(Component)]
struct RelatedMedia {
    entity: Entity,
}

/// Fired when a media entity is selected.
#[derive(Event)]
struct SelectionEvent(Entity);





fn main() {
    App::new()
        .add_plugins(DefaultPlugins)
        .add_plugins(DefaultPickingPlugins)
        .add_plugins(TextMeshPlugin)
        .add_event::<SelectionEvent>()
        .add_systems(Startup, setup)
        .add_systems(Update, spawn_children_on_click)

        .add_systems(Update, (animate_bubbles, highlight_related_media))
        .run();
}

/// Set up the camera and spawn an example speech bubble.
fn setup(
    mut commands: Commands,
    mut meshes: ResMut<Assets<Mesh>>,
    mut materials: ResMut<Assets<ColorMaterial>>,
    asset_server: Res<AssetServer>,
    mut selection_writer: EventWriter<SelectionEvent>,
) {
    commands.spawn((Camera2dBundle::default(), PickingCameraBundle::default()));

    let parent = spawn_speech_bubble(

    let media_entity = commands.spawn_empty().id();

    let bubble_entity = spawn_speech_bubble(
        &mut commands,
        &mut meshes,
        &mut materials,
        &asset_server,
        "Hello, Bevy!",
        Vec3::ZERO,
        true,
    );

    commands
        .entity(parent)
        .insert((PickableBundle::default(), BubbleChildren::default()));
}

/// Spawn child bubbles when a parent bubble is clicked, or toggle visibility if
/// the children already exist.
fn spawn_children_on_click(
    mut commands: Commands,
    mut meshes: ResMut<Assets<Mesh>>,
    mut materials: ResMut<Assets<ColorMaterial>>,
    asset_server: Res<AssetServer>,
    mut events: EventReader<Pointer<Click>>,
    mut parents: Query<(&mut BubbleChildren, &Transform)>,
    mut visibility: Query<&mut Visibility>,
) {
    for ev in events.read() {
        if let Ok((mut children, transform)) = parents.get_mut(ev.target) {
            if children.0.is_empty() {
                let offsets = [Vec3::X * 200.0, Vec3::Z * 200.0];
                for offset in offsets {
                    let child = spawn_speech_bubble(
                        &mut commands,
                        &mut meshes,
                        &mut materials,
                        &asset_server,
                        "Child Bubble",
                        transform.translation + offset,
                        false,
                    );
                    children.0.push(child);
                }
            } else {
                for &child in &children.0 {
                    if let Ok(mut vis) = visibility.get_mut(child) {
                        *vis = match *vis {
                            Visibility::Hidden => Visibility::Visible,
                            _ => Visibility::Hidden,
                        };
                    }
                }
            }
        }
    }
    commands.entity(bubble_entity).insert(RelatedMedia {
        entity: media_entity,
    });

    selection_writer.send(SelectionEvent(media_entity));
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
    commands.spawn((MaterialMesh2dBundle {
        mesh: shadow_mesh.clone().into(),
        material: materials.add(Color::rgba(0.0, 0.0, 0.0, 0.2).into()),
        transform: Transform::from_translation(position + Vec3::new(5.0, -5.0, -0.1)),
        ..default()
    },));

    // main bubble
    let bubble_entity = commands
        .spawn((MaterialMesh2dBundle {
            mesh: bubble_mesh.into(),
            material: materials.add(Color::rgb(0.96, 0.96, 0.96).into()),
            transform: Transform::from_translation(position),
            ..default()
        },))

        .spawn((
            MaterialMesh2dBundle {
                mesh: bubble_mesh.into(),
                material: materials.add(Color::rgb(0.96, 0.96, 0.96).into()),
                transform: Transform::from_translation(position),
                ..default()
            },
            BubbleAnimation::default(),
        ))
        .id();

    // optional tail
    if with_tail {
        commands.spawn((MaterialMesh2dBundle {
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
        },));
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


/// Interpolates bubble scale toward its target.
fn animate_bubbles(time: Res<Time>, mut query: Query<(&mut Transform, &BubbleAnimation)>) {
    for (mut transform, anim) in &mut query {
        if transform.scale != anim.target_scale {
            transform.scale = transform
                .scale
                .lerp(anim.target_scale, time.delta_seconds() * 5.0);
        }
    }
}

/// Highlights bubbles whose related media has been selected.
fn highlight_related_media(
    mut events: EventReader<SelectionEvent>,
    mut query: Query<(
        &RelatedMedia,
        &mut Handle<ColorMaterial>,
        &mut BubbleAnimation,
    )>,
    mut materials: ResMut<Assets<ColorMaterial>>,
) {
    for SelectionEvent(selected) in events.iter() {
        for (related, material, mut anim) in &mut query {
            let is_selected = related.entity == *selected;
            anim.highlight = is_selected;
            anim.target_scale = if is_selected {
                Vec3::splat(1.2)
            } else {
                Vec3::ONE
            };
            if let Some(mat) = materials.get_mut(material) {
                mat.color = if is_selected {
                    Color::YELLOW
                } else {
                    Color::rgb(0.96, 0.96, 0.96)
                };
            }
        }
    }
}

