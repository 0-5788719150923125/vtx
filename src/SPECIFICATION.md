Which are good methods to use for a self-correcting program?

I would like to write a program that performs a corrective action based on current state, history of actions taken, and state history.

Examples:

- navigating a ship: control engine power and rudder position, with sensors for speed, direction, location, and a goal function of reaching a location, and maybe speed. This can be a chaotic environment affected by changing weather conditions and so on. Feedback loop is slow, long, and with a complex cyclical relationship.

- room heating: control heat output, with sensor for temperature. It's easy to overcorrect and overheat. Opening a window would require a much higher heat output, but only temporarily.

The goal is to have a simple general purpose approach that can be trained, but which can also adapt to new conditions, to reduce manual programming/configuration of control logic. It basically has to learn (discover) an equation that includes linear, sinusoidal, logarithmic/exponetial, and time components.

Maybe neural networks? Which current libraries/algorithms are most relevant? sklearn?

src: https://www.reddit.com/r/learnmachinelearning/comments/18bmj7o