use bevy_app::{App, Update};
use bevy_ecs::prelude::*;

#[derive(Resource, Default)]
struct ChildState {
    entity: Option<Entity>,
    spawn_count: u32,
}

#[derive(Component)]
struct Child;

#[derive(Component)]
struct Visible(pub bool);

#[derive(Event)]
struct Click;

fn toggle_child(
    mut commands: Commands,
    mut clicks: EventReader<Click>,
    mut state: ResMut<ChildState>,
    mut query: Query<&mut Visible, With<Child>>,
) {
    for _ in clicks.read() {
        match state.entity {
            Some(id) => {
                if let Ok(mut vis) = query.get_mut(id) {
                    vis.0 = !vis.0;
                }
            }
            None => {
                let child = commands.spawn((Child, Visible(true))).id();
                state.entity = Some(child);
                state.spawn_count += 1;
            }
        }
    }
}

#[test]
fn spawns_and_toggles_child_on_click() {
    let mut app = App::new();
    app.add_event::<Click>()
        .init_resource::<ChildState>()
        .add_systems(Update, toggle_child);

    // First click spawns the child entity
    app.world.send_event(Click);
    app.update();
    let state = app.world.resource::<ChildState>();
    let child = state.entity.expect("child should spawn on first click");
    assert_eq!(state.spawn_count, 1);
    assert!(app.world.get::<Visible>(child).unwrap().0);
    let _ = state;

    // Second click toggles visibility without spawning a new child
    app.world.send_event(Click);
    app.update();
    let state = app.world.resource::<ChildState>();
    assert_eq!(state.spawn_count, 1);
    assert_eq!(state.entity.unwrap(), child);
    assert!(!app.world.get::<Visible>(child).unwrap().0);
    let _ = state;

    // Third click toggles visibility back on
    app.world.send_event(Click);
    app.update();
    let state = app.world.resource::<ChildState>();
    assert_eq!(state.spawn_count, 1);
    assert_eq!(state.entity.unwrap(), child);
    assert!(app.world.get::<Visible>(child).unwrap().0);
}
