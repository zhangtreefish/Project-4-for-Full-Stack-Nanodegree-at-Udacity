import React, { PropTypes } from 'react';

import styles from './index.module.scss';
import cssModules from 'react-css-modules';
import Box from 'grommet-udacity/components/Box';
import Paragraph from 'grommet-udacity/components/Paragraph';

const Game = ({
  game,
}) => (
  <Box>
    <Paragraph> name:{game.name} </Paragraph>
    <Paragraph> seatsAvailable:{game.seatsAvailable} </Paragraph>
    <Paragraph> playerOne:{game.playerOne} </Paragraph>
    <Paragraph> playerTwo:{game.playerTwo} </Paragraph>
    <Paragraph> gameCurrentMove:{game.gameCurrentMove} </Paragraph>
    <Paragraph> gameBoard:{game.gameBoard} </Paragraph>
  </Box>
);

Game.propTypes = {
  game: PropTypes.object.isRequired,
};

export default cssModules(Game, styles);
