use bevy::prelude::*;

#[derive(Component, Clone, Debug)]
pub struct TimelineItem {
    pub id: u64,
    pub timestamp: f64,
    pub medium: String,
    pub participants: Vec<String>,
    pub content: String,
}

const PIXELS_PER_SECOND: f32 = 10.0;

pub fn time_to_y(base_time: f64, timestamp: f64) -> f32 {
    ((timestamp - base_time) as f32) * PIXELS_PER_SECOND
}

pub fn spawn_timeline(mut commands: Commands, items: Res<Vec<TimelineItem>>) {
    if items.is_empty() {
        return;
    }

    let start_time = items[0].timestamp;
    for item in items.iter() {
        let y = time_to_y(start_time, item.timestamp);
        commands
            .spawn((
                Transform::from_xyz(0.0, y, 0.0),
                GlobalTransform::default(),
                item.clone(),
            ));
    }
}

