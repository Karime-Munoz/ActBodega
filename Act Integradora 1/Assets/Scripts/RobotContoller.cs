using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class RobotController : MonoBehaviour
{
    public Animator animator;
    public float speed = 2.0f;
    private Vector3 targetPosition;
    private bool isMoving = false;

    void Start()
    {
        targetPosition = transform.position;
    }


    void Update()
    {
        if (isMoving)
        {
            MoveTowardsTarget();
        }
    }

    public void SetTargetPosition(Vector3 newPosition)
    {
        if (newPosition == targetPosition)
        {
            Debug.Log($"El robot ya está en la posición objetivo {newPosition}");
            return;
        }
        targetPosition = newPosition;
        isMoving = true;
        animator.SetBool("isRunning", true);
        Debug.Log($"Nuevo objetivo asignado: {newPosition}");
    }
    public bool IsMoving()
    {
        return isMoving;
    }

    private void MoveTowardsTarget()
    {
        float step = speed * Time.deltaTime;
        transform.position = Vector3.MoveTowards(transform.position, targetPosition, step);

        if (Vector3.Distance(transform.position, targetPosition) < 0.01f)
        {
            isMoving = false;
            animator.SetBool("isRunning", false);
        }
    }
}

