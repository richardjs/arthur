This work-in-progress document describes how an Arthur worker
communicates with engines

## Set up

At the start of each work loop, the worker calls the `/worker/start`
endpoint. The server responds with a matchup assignment, telling the
worker to play a game between the specified players.

For each player, the worker clones the git repo specified by the Arthur
configuration, checks out the commit given to it by the matchup data,
and builds the engine.

## Game

The worker calls the engine binary with the initial state as the
argument. The engine should tell the worker its move by outputting a
line to stderr with the form `next: <state after move>`. Case and
whitespace is ignored (apart from anything specific to the state
represntation). The worker then calls the next player's binary with the
new state.

When a terminal state is reached, the engine should output a line to
stderr with the form `result: <win|loss|draw>`. The engine need not
output a `next` line if there is a result line.

All other output to stderr, and any output to stdout, is logged but
otherwise ignored by the worker.

The worker sends logs to the server after every engine move.

## Postgame

The worker sends the results to the server, and starts a new work loop.
