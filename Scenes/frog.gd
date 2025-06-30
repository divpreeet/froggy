extends CharacterBody2D

@export var speed: float = 150.0

func _physics_process(delta: float) -> void:
	var direction: Vector2 = Vector2.ZERO

	if Input.is_action_pressed("move_left"):
		direction.x = -1
	elif Input.is_action_pressed("move_right"):
		direction.x = 1

	if direction.length() > 0:
		direction = direction.normalized()

	velocity = direction * speed

	move_and_slide()
