import json
import numpy as np
from PIL import Image
import os


def load_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def load_txt_file(file_path):
    with open(file_path, 'r') as file:
        return set(line.strip() for line in file)

def find_exercise(exercises, exercise_name):
    for exercise in exercises:
        if exercise['name'].lower() == exercise_name.lower():
            return exercise
    return None

def get_relevant_visuals(muscle_group_visuals, muscle):
    for item in muscle_group_visuals:
        if item['muscle_group'].lower() == muscle.lower():
            return item['relevant_visuals']
    return []

def split_visuals(visuals, back_visuals, front_visuals):
    relevant_visuals_back = [v for v in visuals if v in back_visuals]
    relevant_visuals_front = [v for v in visuals if v in front_visuals]
    for v in visuals:
        if v not in back_visuals and v not in front_visuals:
            print(f"Warning: Visual '{v}' not found in back or front visuals")
    return relevant_visuals_back, relevant_visuals_front

def get_exercise_visuals(exercise_name):
    # Load necessary data
    all_exercises = load_json_file('allExercises.json')["data"]["allExercises"]
    muscle_group_visuals = load_json_file('muscle_group_visuals.json')
    back_visuals = load_txt_file('visuals_back.txt')
    front_visuals = load_txt_file('visuals_front.txt')

    # Find the exercise
    exercise = find_exercise(all_exercises, exercise_name)
    print(f"Exercise '{exercise_name}' found:", exercise)
    if not exercise:
        return [], []

    # Get primary muscles
    primary_muscles = exercise['primaryMuscles']
    print(f"Primary muscles for '{exercise_name}':", primary_muscles)

    # Get relevant visuals for each primary muscle
    all_relevant_visuals = []
    for muscle in primary_muscles:
        all_relevant_visuals.extend(get_relevant_visuals(muscle_group_visuals, muscle))
    print(f"Relevant visuals for '{exercise_name}':", all_relevant_visuals)

    # Split visuals into back and front
    return split_visuals(all_relevant_visuals, back_visuals, front_visuals)



def create_overlay_image(visual_list, view_type, exercise_name):
    base_image_path = f'visual_base_{view_type}.png'
    if not os.path.exists(base_image_path):
        raise FileNotFoundError(f"Base image not found: {base_image_path}")
    
    base_image = Image.open(base_image_path).convert('RGBA')
    overlay = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
    
    for visual in visual_list:
        image_path = os.path.join('visuals', f'all_{view_type}', f'{visual}.png')
        if os.path.exists(image_path):
            with Image.open(image_path) as layer:
                layer = layer.convert('RGBA')
                layer = layer.resize(base_image.size, Image.Resampling.LANCZOS)
                
                layer_array = np.array(layer)
                
                red_mask = (layer_array[:,:,0] > 200) & (layer_array[:,:,1] < 50) & (layer_array[:,:,2] < 50)
                
                layer_array[~red_mask] = [0, 0, 0, 0]
                layer_array[red_mask] = [255, 0, 0, 128]
                
                red_layer = Image.fromarray(layer_array)
                overlay = Image.alpha_composite(overlay, red_layer)
    
    final_image = Image.alpha_composite(base_image, overlay)
    
    # Create output directory if it doesn't exist
    os.makedirs('output_visuals', exist_ok=True)
    
    # Create filename with exercise name
    safe_exercise_name = exercise_name.replace(' ', '_').lower()
    output_path = os.path.join('output_visuals', f'exercise_{safe_exercise_name}_{view_type}.png')
    
    final_image.save(output_path)
    print(f"Saved {view_type} overlay image to {output_path}")
    return output_path

def visualize_exercise_muscles(back_visuals, front_visuals, exercise_name):
    back_image_path = create_overlay_image(back_visuals, 'back', exercise_name)
    front_image_path = create_overlay_image(front_visuals, 'front', exercise_name)
    return back_image_path, front_image_path


if __name__ == "__main__":
    exercise_name = "smith machine curl"
    back_visuals, front_visuals = get_exercise_visuals(exercise_name)

    print(f"Relevant visuals for '{exercise_name}':")
    print("Back visuals:", back_visuals)
    print("Front visuals:", front_visuals)

    back_image, front_image = visualize_exercise_muscles(back_visuals, front_visuals, exercise_name)
    print(f"\nOverlay images created:")
    print(f"Back view: {back_image}")
    print(f"Front view: {front_image}")

    # Test with an exercise that doesn't exist
    exercise_name = "nonexistent exercise"
    back_visuals, front_visuals = get_exercise_visuals(exercise_name)

    print(f"\nRelevant visuals for '{exercise_name}':")
    print("Back visuals:", back_visuals)
    print("Front visuals:", front_visuals)

    if back_visuals or front_visuals:
        visualize_exercise_muscles(back_visuals, front_visuals, exercise_name)

