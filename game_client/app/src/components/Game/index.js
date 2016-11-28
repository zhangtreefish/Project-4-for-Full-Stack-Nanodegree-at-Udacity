import React, { PropTypes } from 'react';

import styles from './index.module.scss';
import cssModules from 'react-css-modules';
import Box from 'grommet-udacity/components/Box';
import Paragraph from 'grommet-udacity/components/Paragraph';

const Game = ({
  game,
}) => (
  <Box colorIndex="accent-2-a">
    <Paragraph size="large"> name:{game.name} </Paragraph>
    <Paragraph size="large"> seatsAvailable:{game.seatsAvailable} </Paragraph>
    <Paragraph size="large"> playerOne:{game.playerOne} </Paragraph>
    <Paragraph size="large"> playerTwo:{game.playerTwo} </Paragraph>
    <Paragraph size="large"> gameCurrentMove:{game.gameCurrentMove} </Paragraph>
    <Paragraph size="large"> gameBoard:{game.gameBoard} </Paragraph>
  </Box>
);

Game.propTypes = {
  game: PropTypes.object.isRequired,
};

export default cssModules(Game, styles);
