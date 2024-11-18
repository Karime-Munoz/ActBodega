using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class RobotController : MonoBehaviour
{
    public Animator animator;
    public float speed = 2.0f;
    private Vector3 targetPosition;
    private bool isMoving = false;
    // Start is called before the first frame update
    void Start()
    {
        targetPosition = transform.position;
    }

    // Update is called once per frame
    void Update()
    {
        if (isMoving)
        {
            MoveTowardsTarget();
        }
    }

    public void SetTargetPosition(Vector3 newPosition)
    {
        targetPosition = newPosition;
        isMoving = true;
        animator.SetBool("isRunning", true);
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

