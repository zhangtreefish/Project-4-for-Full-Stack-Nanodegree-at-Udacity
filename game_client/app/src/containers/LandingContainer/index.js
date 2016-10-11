import React, { PropTypes, Component } from 'react';
/* eslint-disable import/no-unresolved */
import {
  LogoImage,
  Header,
} from 'components';
/* eslint-enable import/no-unresolved */
import styles from './index.module.scss';
import cssModules from 'react-css-modules';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import * as MyActions from './actions';

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
          <div>
            <LogoImage
              imageSource="https://d30y9cdsu7xlg0.cloudfront.net/png/76612-200.png"
            />
            <div className={styles.headerText}>
              <Header
                content="Scaling the Front End feature first with the tictactoe game!"
              />
            </div>
          </div>
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
