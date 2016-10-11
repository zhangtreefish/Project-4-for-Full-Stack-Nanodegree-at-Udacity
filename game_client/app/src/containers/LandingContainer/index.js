import React, { PropTypes, Component } from 'react';
/* eslint-disable import/no-unresolved */
import { Game } from 'components';
/* eslint-enable import/no-unresolved */
import styles from './index.module.scss';
import cssModules from 'react-css-modules';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import * as MyActions from './actions';
import Heading from 'grommet-udacity/components/Heading';
import Box from 'grommet-udacity/components/Box';
import Section from 'grommet-udacity/components/Section';
import Tiles from 'grommet-udacity/components/Tiles';
import Tile from 'grommet-udacity/components/Tile';

export class LandingContainer extends Component {
  constructor(props) {
    super(props);
    this.initiateLoading = this.initiateLoading.bind(this);
  }
  componentDidMount() {
    this.initiateLoading();
  }
  initiateLoading() {
    const {
      loadGames,
    } = this.props.actions;
    loadGames();
  }
  render() {
    const {
      isLoading,
      games,
    } = this.props;
    return (
      <div className={styles.container}>
        {isLoading ?
          <h1>LOADING...</h1>
        :
          <Section pad="small" direction="column" pad={{ vertical: 'medium' }}>
            <Heading tag="h2" align="center">
              Games
            </Heading>
            <Box pad={{ vertical: 'small' }} direction="row">
              <Tiles flush fill className={styles.mainSection}>
                {games.map((game, i) =>
                  <Tile
                    key={i}
                    align="start"
                    basis="small"
                    direction="row"
                    separator="bottom"
                    className={styles.game}
                  >
                    <Game game={game} />
                  </Tile>
                )}
              </Tiles>
            </Box>
          </Section>
        }
      </div>
    );
  }
}

LandingContainer.propTypes = {
  actions: PropTypes.object.isRequired,
  isLoading: PropTypes.bool.isRequired,
  games: PropTypes.array,
};

// mapStateToProps :: {State} -> {Action}
const mapStateToProps = (state) => ({
  isLoading: state.landingReducer.isLoading,
  games: state.landingReducer.games,
});

// mapDispatchToProps :: Dispatch Func -> {Actions}
const mapDispatchToProps = (dispatch) => ({
  actions: bindActionCreators(MyActions, dispatch),
});

const StyledContainer = cssModules(LandingContainer, styles);

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(StyledContainer);
